from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Protocol

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.db.base import new_id, utc_now
from tsuyulabo_api.db.research import Job
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.backpressure import admit_job

JobFunction = Callable[[dict[str, Any]], dict[str, Any] | Awaitable[dict[str, Any]]]


async def create_job(session: AsyncSession, user_id: str, kind: str) -> Job:
    settings = session.info.get("guard_settings")
    if settings is not None:
        await admit_job(session, user_id, settings)
    job = Job(id=new_id(), user_id=user_id, kind=kind, status="pending")
    session.add(job)
    await session.flush()
    return job


async def get_job(session: AsyncSession, user_id: str, job_id: str) -> Job:
    job = await session.scalar(select(Job).where(Job.id == job_id, Job.user_id == user_id))
    if job is None:
        raise APIError("not_found", "ジョブが見つかりません", 404)
    return job


async def finish_job(
    session: AsyncSession,
    job: Job,
    *,
    result: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    job.status = "failed" if error is not None else "succeeded"
    job.result, job.error, job.finished_at = result, error, utc_now()
    await session.flush()


class JobQueue(Protocol):
    async def enqueue(self, job_id: str, kind: str, params: dict[str, Any]) -> None: ...

    async def close(self) -> None: ...


class InlineJobQueue:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], handlers: Mapping[str, JobFunction]
    ) -> None:
        self.sessions = sessions
        self.handlers = handlers

    async def enqueue(self, job_id: str, kind: str, params: dict[str, Any]) -> None:
        # The row is committed before dispatch, so inline and Redis consumers see it.
        async with self.sessions() as session, session.begin():
            job = await session.scalar(select(Job).where(Job.id == job_id).with_for_update())
            if job is None:
                raise APIError("not_found", "ジョブが見つかりません", 404)
            if job.status != "pending":
                return
            job.status = "running"
        try:
            function = self.handlers[kind]
            result = function(params)
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, dict):
                raise TypeError("job handlers must return a JSON object")
        except Exception:
            async with self.sessions() as session, session.begin():
                job = await session.get(Job, job_id)
                await finish_job(
                    session, job, error={"code": "job_failed", "message": "処理に失敗しました"}
                )
        else:
            async with self.sessions() as session, session.begin():
                job = await session.get(Job, job_id)
                await finish_job(session, job, result=result)

    async def close(self) -> None:
        pass


class ArqJobQueue:
    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self.pool: ArqRedis | None = None

    async def enqueue(self, job_id: str, kind: str, params: dict[str, Any]) -> None:
        if self.pool is None:
            self.pool = await create_pool(RedisSettings.from_dsn(self.redis_url))
        await self.pool.enqueue_job("run_brain_job", job_id, kind, params, _job_id=job_id)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.aclose()


class BrainClient:
    """Owns job persistence and dispatch; call outside an open mutation transaction.

    W2 routes needing atomic domain effects should create_job in their transaction,
    then dispatch the committed ID through JobQueue (or a durable outbox).
    """

    def __init__(self, sessions: async_sessionmaker[AsyncSession], queue: JobQueue) -> None:
        self.sessions, self.queue = sessions, queue

    async def submit(self, user_id: str, kind: str, params: dict[str, Any]) -> Job:
        async with self.sessions() as session, session.begin():
            job = await create_job(session, user_id, kind)
            job.params = params
            job_id = job.id
        try:
            await self.queue.enqueue(job_id, kind, params)
        except Exception:
            async with self.sessions() as session, session.begin():
                job = await session.get(Job, job_id)
                await finish_job(
                    session,
                    job,
                    error={"code": "enqueue_failed", "message": "ジョブを送信できませんでした"},
                )
        async with self.sessions() as session:
            return await get_job(session, user_id, job_id)
