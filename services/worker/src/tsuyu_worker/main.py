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
from tsuyulabo_api.settings import Settings

from . import jobs
from .schedule import nightly_memos


async def startup(ctx: dict[str, Any]) -> None:
    engine = create_engine(Settings().database_url)
    ctx["engine"] = engine
    ctx["sessions"] = session_factory(engine)
    ctx["provider"] = default_provider()


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
        )
    ]
    timezone = JST
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 180
