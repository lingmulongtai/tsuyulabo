"""Redis-free entry points. arq wrappers live in main.py."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_shiori.features import JST, answer_question, morning_memo
from tsuyu_shiori.gateway import Provider
from tsuyu_shiori.tools import ExperimentArguments
from tsuyulabo_api.db.models import Job, ShioriMessage, User
from tsuyulabo_api.db.session import create_engine, session_factory
from tsuyulabo_api.settings import Settings

from .adapters import SQLLab, SQLRecordStore, conversation_scope
from .brain_adapter import BrainEngine

Sessions = async_sessionmaker[AsyncSession]
Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@asynccontextmanager
async def session_source(sessions: Sessions | None) -> AsyncIterator[Sessions]:
    if sessions is not None:
        yield sessions
    else:
        engine = create_engine(Settings().database_url)
        try:
            yield session_factory(engine)
        finally:
            await engine.dispose()


async def perform(
    session: AsyncSession,
    user_id: str,
    kind: str,
    params: dict[str, Any],
    provider: Provider | None,
    brain: BrainEngine | None,
) -> dict[str, Any]:
    store = SQLRecordStore(session, user_id)
    lab = SQLLab(session, user_id, brain)
    week_id, fly_id = await conversation_scope(store, params)
    if kind == "brain_run_experiment":
        arguments = ExperimentArguments.model_validate(
            {
                "fly_id": fly_id,
                "cue": params.get("cue", "banana"),
                "trials": params.get("trials", 20),
                "seed": params.get("seed", 0),
            }
        )
        record = await lab.run_odor_choice(**arguments.model_dump())
        return {
            "experiment_id": record.id,
            "evidence": [record.id],
            "experiments": [record.id],
            "result": record.data,
            "cost": {"usd": 0.0},
        }
    if kind != "shiori_answer":
        raise ValueError("unknown job kind")
    question = params.get("question")
    if not isinstance(question, str):
        raise ValueError("question is required")
    answer = await answer_question(
        question, store=store, lab=lab, week_id=week_id, fly_id=fly_id, provider=provider
    )
    session.add_all(
        [
            ShioriMessage(user_id=user_id, role="user", text=question, evidence=[], cost={}),
            ShioriMessage(
                user_id=user_id,
                role="assistant",
                text=answer.text,
                evidence=answer.evidence_ids,
                cost=answer.cost,
            ),
        ]
    )
    await session.flush()
    return answer.to_dict()


async def run_job(
    job_id: str,
    kind: str,
    *,
    sessions: Sessions | None = None,
    params: dict[str, Any] | None = None,
    provider: Provider | None = None,
    brain: BrainEngine | None = None,
) -> dict[str, Any]:
    async with session_source(sessions) as factory, factory() as session, session.begin():
        job = await session.scalar(select(Job).where(Job.id == job_id).with_for_update())
        if job is None:
            raise ValueError("job not found")
        if job.status in {"succeeded", "failed"}:
            return job.result or {"error": job.error}
        # The row lock lasts until status, messages and experiments commit together.
        # A process crash rolls back everything, leaving the job retryable as pending.
        job.status = "running"
        try:
            async with session.begin_nested():
                if job.kind != kind:
                    raise ValueError("job kind does not match handler")
                inputs = params if params is not None else (job.result or {}).get("input", {})
                result = await perform(session, job.user_id, kind, inputs, provider, brain)
        except Exception:
            job.status, job.result = "failed", None
            job.error = {"code": "job_failed", "message": "処理に失敗しました"}
            result = {"error": job.error}
        else:
            job.status, job.result, job.error = "succeeded", result, None
        job.finished_at = datetime.now(UTC)
        await session.flush()
        return result


async def brain_run_experiment(
    job_id: str,
    *,
    sessions: Sessions | None = None,
    params: dict[str, Any] | None = None,
    brain: BrainEngine | None = None,
) -> dict[str, Any]:
    return await run_job(
        job_id, "brain_run_experiment", sessions=sessions, params=params, brain=brain
    )


async def shiori_answer(
    job_id: str,
    *,
    sessions: Sessions | None = None,
    params: dict[str, Any] | None = None,
    provider: Provider | None = None,
    brain: BrainEngine | None = None,
) -> dict[str, Any]:
    return await run_job(
        job_id, "shiori_answer", sessions=sessions, params=params, provider=provider, brain=brain
    )


async def shiori_morning_memo(
    user_id: str,
    *,
    sessions: Sessions | None = None,
    provider: Provider | None = None,
    brain: BrainEngine | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    day_start = now.astimezone(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    async with session_source(sessions) as factory, factory() as session, session.begin():
        user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            raise ValueError("user not found")
        existing = await session.scalar(
            select(ShioriMessage).where(
                ShioriMessage.user_id == user_id,
                ShioriMessage.role == "morning_memo",
                ShioriMessage.created_at >= day_start,
                ShioriMessage.created_at < day_start + timedelta(days=1),
            )
        )
        if existing is not None:
            return {
                "text": existing.text,
                "evidence": existing.evidence,
                "cost": existing.cost,
                "message_id": existing.id,
                "reused": True,
            }
        store = SQLRecordStore(session, user_id)
        try:
            week_id, fly_id = await conversation_scope(store, {})
        except ValueError:
            return {"skipped": "no_active_week"}
        answer = await morning_memo(
            store=store,
            lab=SQLLab(session, user_id, brain),
            week_id=week_id,
            fly_id=fly_id,
            provider=provider,
            now=now,
        )
        message = ShioriMessage(
            user_id=user_id,
            role="morning_memo",
            text=answer.text,
            evidence=answer.evidence_ids,
            cost=answer.cost,
            created_at=now,
        )
        session.add(message)
        await session.flush()
        return {**answer.to_dict(), "message_id": message.id, "reused": False}


def inline_handlers(
    sessions: Sessions,
    user_id: str,
    *,
    provider: Provider | None = None,
    brain: BrainEngine | None = None,
) -> dict[str, Handler]:
    """Bind handlers for the existing API InlineJobQueue, which owns job status itself.

    Bind user_id from the authenticated host, never from LLM or request parameters.
    """

    def handler(kind: str) -> Handler:
        async def invoke(params: dict[str, Any]) -> dict[str, Any]:
            async with sessions() as session, session.begin():
                return await perform(session, user_id, kind, params, provider, brain)

        return invoke

    return {kind: handler(kind) for kind in ("brain_run_experiment", "shiori_answer")}
