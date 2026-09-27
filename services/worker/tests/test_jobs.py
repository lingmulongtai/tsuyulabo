from __future__ import annotations

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_shiori.gateway import MockProvider, Response, ToolCall
from tsuyu_worker.brain_adapter import FakeBrainEngine
from tsuyu_worker.jobs import brain_run_experiment, inline_handlers, shiori_answer
from tsuyulabo_api.db.models import Experiment, Job, ShioriMessage
from tsuyulabo_api.services.jobs import BrainClient, InlineJobQueue


async def create_job(
    sessions: async_sessionmaker[AsyncSession], job_id: str, kind: str, params: dict
) -> None:
    async with sessions() as session, session.begin():
        session.add(Job(id=job_id, user_id="u", kind=kind, result={"input": params}))


async def test_jobs_persist_and_duplicate_delivery_is_idempotent(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    await create_job(sessions, "exp", "brain_run_experiment", {"fly_id": "f", "cue": "banana"})
    results = await asyncio.gather(
        *[brain_run_experiment("exp", sessions=sessions, brain=FakeBrainEngine()) for _ in range(2)]
    )
    assert results[0] == results[1]
    assert results[0]["result"]["toward"] == 15
    await create_job(sessions, "answer", "shiori_answer", {"question": "しつけは何回？"})
    answer = await shiori_answer("answer", sessions=sessions, provider=MockProvider())
    assert "1回" in answer["answer"]
    assert answer["verification"]["rate"] == 1
    await shiori_answer("answer", sessions=sessions, provider=MockProvider())
    async with sessions() as session:
        job = await session.get(Job, "answer")
        assert job.status == "succeeded" and job.finished_at is not None
        assert job.result["cost"]["usd"] == 0
        assert await session.scalar(select(func.count()).select_from(ShioriMessage)) == 2
        assert await session.scalar(select(func.count()).select_from(Experiment)) == 1


async def test_failed_job_rolls_back_experiment_and_hides_exception(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    class BrokenProvider(MockProvider):
        calls = 0

        async def complete(self, messages: list, tools: list, model: str) -> Response:
            self.calls += 1
            if self.calls == 1:
                return Response(
                    tool_calls=[
                        ToolCall("exp", "run_odor_choice", {"fly_id": "f", "cue": "banana"})
                    ]
                )
            raise RuntimeError("private credentials")

    await create_job(sessions, "broken", "shiori_answer", {"fly_id": "f", "question": "実験"})
    result = await shiori_answer(
        "broken", sessions=sessions, provider=BrokenProvider(), brain=FakeBrainEngine()
    )
    assert result["error"]["code"] == "job_failed"
    assert "private" not in str(result)
    async with sessions() as session:
        assert (await session.get(Job, "broken")).status == "failed"
        assert await session.scalar(select(func.count()).select_from(Experiment)) == 0
        assert await session.scalar(select(func.count()).select_from(ShioriMessage)) == 0


async def test_foreign_fly_is_rejected_and_queue_inline_contract_works(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    await create_job(sessions, "foreign", "brain_run_experiment", {"fly_id": "other-w"})
    assert "error" in await brain_run_experiment(
        "foreign", sessions=sessions, brain=FakeBrainEngine()
    )
    queue = InlineJobQueue(sessions, inline_handlers(sessions, "u", provider=MockProvider()))
    result = await BrainClient(sessions, queue).submit("u", "shiori_answer", {"question": "何回？"})
    assert result.status == "succeeded"
    assert "1回" in result.result["answer"]
