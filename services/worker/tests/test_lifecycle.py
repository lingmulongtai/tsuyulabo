from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_shiori.features import JST
from tsuyu_shiori.gateway import MockProvider, Response
from tsuyu_worker.jobs import shiori_answer, shiori_morning_memo
from tsuyu_worker.schedule import nightly_memos
from tsuyulabo_api.db.models import Job, ShioriMessage, Week


async def test_batch_continues_after_one_user_fails(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    class FailingForOneUser(MockProvider):
        async def complete(self, messages: list, tools: list, model: str) -> Response:
            request = json.loads(next(m["content"] for m in messages if m["role"] == "user"))
            if request["week_id"] == "w":
                raise RuntimeError("provider failure")
            return await super().complete(messages, tools, model)

    result = await nightly_memos(
        sessions=sessions,
        provider=FailingForOneUser(),
        now=datetime(2026, 9, 27, 3, 30, tzinfo=JST),
    )
    assert result["failed"] == ["u"]
    assert result["generated"] == ["other"]
    async with sessions() as session:
        assert (
            await session.scalar(
                select(func.count()).select_from(ShioriMessage).where(ShioriMessage.user_id == "u")
            )
            == 0
        )


async def test_no_active_week_and_wrong_job_handler(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with sessions() as session, session.begin():
        week = await session.get(Week, "w")
        week.status = "eclosed"
        session.add(Job(id="wrong-kind", user_id="u", kind="brain_run_experiment"))
    memo = await shiori_morning_memo("u", sessions=sessions, provider=MockProvider())
    assert memo == {"skipped": "no_active_week"}
    result = await shiori_answer("wrong-kind", sessions=sessions, params={"question": "何回？"})
    assert result["error"]["code"] == "job_failed"
    async with sessions() as session:
        job = await session.get(Job, "wrong-kind")
        assert job.status == "failed" and job.finished_at is not None
