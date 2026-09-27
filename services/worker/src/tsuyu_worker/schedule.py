from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select, union
from tsuyu_shiori.gateway import Provider
from tsuyulabo_api.db.models import CareEvent, Job, Puzzle, SleepSession, User

from .jobs import Sessions, session_source, shiori_morning_memo

logger = logging.getLogger(__name__)


async def active_users(sessions: Sessions, now: datetime) -> list[str]:
    """Activity observable in the current schema; generated memos never count as activity."""
    since = now - timedelta(hours=24)
    query = union(
        select(User.id).where(User.created_at >= since, User.created_at <= now),
        select(CareEvent.user_id).where(CareEvent.created_at >= since, CareEvent.created_at <= now),
        select(Job.user_id).where(Job.created_at >= since, Job.created_at <= now),
        select(Puzzle.user_id).where(
            or_(Puzzle.issued_at.between(since, now), Puzzle.submitted_at.between(since, now))
        ),
        select(SleepSession.user_id).where(
            or_(
                SleepSession.started_at.between(since, now),
                SleepSession.ended_at.between(since, now),
            )
        ),
    )
    async with sessions() as session:
        return sorted(await session.scalars(query))


async def nightly_memos(
    *,
    sessions: Sessions | None = None,
    provider: Provider | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    generated, reused, skipped, failed = [], [], [], []
    async with session_source(sessions) as factory:
        for user_id in await active_users(factory, now):
            try:
                result = await shiori_morning_memo(
                    user_id, sessions=factory, provider=provider, now=now
                )
            except Exception:
                # Isolate user failures so a bad provider response cannot stop the whole batch.
                logger.warning("morning memo generation failed for user %s", user_id)
                failed.append(user_id)
                continue
            if result.get("skipped"):
                skipped.append(user_id)
            elif result["reused"]:
                reused.append(user_id)
            else:
                generated.append(user_id)
    return {"generated": generated, "reused": reused, "skipped": skipped, "failed": failed}
