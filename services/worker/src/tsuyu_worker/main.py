"""Run with: uv run arq tsuyu_worker.main.WorkerSettings."""

from __future__ import annotations

import os
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from arq.worker import func
from tsuyu_shiori.features import JST
from tsuyu_shiori.gateway import default_provider
from tsuyulabo_api.db.session import create_engine, session_factory
from tsuyulabo_api.services.push import WebPushSender
from tsuyulabo_api.settings import Settings

from . import jobs
from .push import send_reminders
from .schedule import nightly_memos


async def startup(ctx: dict[str, Any]) -> None:
    settings = Settings()
    engine = create_engine(settings.database_url)
    ctx["engine"] = engine
    ctx["sessions"] = session_factory(engine)
    ctx["provider"] = default_provider()
    ctx["push_sender"] = (
        WebPushSender(settings)
        if settings.vapid_public_key and settings.vapid_private_key
        else None
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["engine"].dispose()


async def arq_brain_run_experiment(
    ctx: dict[str, Any], job_id: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    return await jobs.brain_run_experiment(
        job_id, sessions=ctx["sessions"], params=params, brain=ctx.get("brain")
    )


async def arq_shiori_answer(
    ctx: dict[str, Any], job_id: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    return await jobs.shiori_answer(
        job_id,
        sessions=ctx["sessions"],
        params=params,
        provider=ctx.get("provider"),
        brain=ctx.get("brain"),
    )


async def arq_shiori_morning_memo(ctx: dict[str, Any], user_id: str) -> dict[str, Any]:
    return await jobs.shiori_morning_memo(
        user_id, sessions=ctx["sessions"], provider=ctx.get("provider")
    )


async def run_brain_job(
    ctx: dict[str, Any], job_id: str, kind: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Compatibility entry point used by the current API ArqJobQueue."""
    return await jobs.run_job(
        job_id,
        kind,
        sessions=ctx["sessions"],
        params=params,
        provider=ctx.get("provider"),
        brain=ctx.get("brain"),
    )


async def nightly_journal(ctx: dict[str, Any]) -> dict[str, Any]:
    return await nightly_memos(sessions=ctx["sessions"], provider=ctx.get("provider"))


async def slot_push(ctx: dict[str, Any]) -> dict[str, Any]:
    if ctx.get("push_sender") is None:
        return {"skipped": "push_disabled"}
    return await send_reminders(ctx["sessions"], ctx["push_sender"])


async def friend_push(ctx: dict[str, Any]) -> dict[str, Any]:
    if ctx.get("push_sender") is None:
        return {"skipped": "push_disabled"}
    return await send_reminders(ctx["sessions"], ctx["push_sender"], friends=True)


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    functions = [
        func(arq_brain_run_experiment, name="brain_run_experiment"),
        func(arq_shiori_answer, name="shiori_answer"),
        func(arq_shiori_morning_memo, name="shiori_morning_memo"),
        run_brain_job,
    ]
    cron_jobs = [
        cron(
            nightly_journal,
            hour=3,
            minute=30,
            second=0,
            microsecond=0,
            run_at_startup=False,
            unique=True,
        ),
        cron(
            slot_push,
            hour={4, 12, 18},
            minute={0, 1, 2, 3, 4},
            second=0,
            microsecond=0,
            run_at_startup=False,
            unique=True,
        ),
        cron(friend_push, minute=None, second=0, microsecond=0, run_at_startup=False, unique=True),
    ]
    timezone = JST
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 180
