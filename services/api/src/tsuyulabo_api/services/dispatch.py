from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.models import Job
from tsuyulabo_api.services.jobs import create_job, finish_job


async def dispatch(request: Request, job_id: str, kind: str, params: dict[str, Any]) -> None:
    # Starlette runs this only after IdempotentRoute has committed its transaction.
    try:
        await request.app.state.job_queue.enqueue(job_id, kind, params)
    except Exception:
        async with request.app.state.session_factory() as session, session.begin():
            job = await session.get(Job, job_id)
            if job.status == "pending":
                await finish_job(
                    session,
                    job,
                    error={"code": "enqueue_failed", "message": "ジョブを送信できませんでした"},
                )


async def enqueue(
    session: AsyncSession,
    request: Request,
    tasks: BackgroundTasks,
    user_id: str,
    kind: str,
    params: dict[str, Any],
) -> Job:
    job = await create_job(session, user_id, kind)
    job.params = params
    await session.flush()
    tasks.add_task(dispatch, request, job.id, kind, params)
    return job
