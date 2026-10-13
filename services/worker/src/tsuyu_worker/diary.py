"""Nightly diary batch includes unattended individuals, and isolates failures."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from tsuyu_shiori.features import JST
from tsuyu_shiori.gateway import Provider
from tsuyulabo_api.db.models import Week
from tsuyulabo_api.services.diary import generate

from .jobs import Sessions, session_source

logger = logging.getLogger(__name__)


async def nightly_diaries(
    *,
    sessions: Sessions | None = None,
    provider: Provider | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    day = now.astimezone(JST).date() - timedelta(days=1)
    start = datetime.combine(day, datetime.min.time(), JST)
    end = start + timedelta(days=1)
    result: dict[str, list[str]] = {key: [] for key in ("generated", "reused", "skipped", "failed")}
    async with session_source(sessions) as factory:
        async with factory() as session:
            weeks = list(
                (
                    await session.execute(
                        select(Week.user_id, Week.id)
                        .where(
                            Week.started_at < end,
                        )
                        .order_by(Week.user_id, Week.started_at)
                    )
                ).all()
            )
        for user_id, week_id in weeks:
            try:
                async with factory() as session, session.begin():
                    entry = await generate(session, user_id, week_id, day, provider=provider)
                key = (
                    "skipped"
                    if entry.get("skipped")
                    else "reused"
                    if entry["reused"]
                    else "generated"
                )
                result[key].append(week_id)
            except Exception:
                logger.warning("diary generation failed for week %s", week_id)
                result["failed"].append(week_id)
    return result
