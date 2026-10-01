"""Reserve job capacity with the job row in the caller's transaction."""

from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.models import Job, User
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.settings import Settings


async def admit_job(session: AsyncSession, user_id: str, settings: Settings) -> None:
    # Keep the existing user -> job lock order, including callers outside game routes.
    await session.scalar(select(User).where(User.id == user_id).with_for_update())
    if session.get_bind().dialect.name == "postgresql":
        # All API processes share this transaction-scoped admission lock. It is released
        # on commit/rollback. SQLite's BEGIN IMMEDIATE already serializes writers.
        await session.execute(text("SELECT pg_advisory_xact_lock(1953724789)"))
    active = select(Job).where(Job.status.in_(["pending", "running"]))
    total = await session.scalar(select(func.count()).select_from(active.subquery()))
    owned = await session.scalar(
        select(func.count()).select_from(active.where(Job.user_id == user_id).subquery())
    )
    if total >= settings.job_max_total or owned >= settings.job_max_per_user:
        raise APIError(
            "server_busy",
            "研究所が混み合っています。少し時間をおいてから、もう一度ためしてね",
            503,
            {"retry_after": settings.job_busy_retry_after},
        )
