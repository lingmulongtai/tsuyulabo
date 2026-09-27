from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.models import SleepSession
from tsuyulabo_api.domain.circadian import Circadian, SleepRecord, summarize
from tsuyulabo_api.domain.constants import CIRCADIAN_WINDOW


async def current(session: AsyncSession, user_id: str, now: datetime) -> Circadian:
    records = await session.scalars(
        select(SleepSession)
        .where(
            SleepSession.user_id == user_id,
            SleepSession.ended_at <= now,
            SleepSession.started_at <= SleepSession.ended_at,
        )
        .order_by(SleepSession.ended_at.desc(), SleepSession.started_at.desc())
        .limit(CIRCADIAN_WINDOW)
    )
    return summarize((SleepRecord(r.started_at, r.ended_at) for r in records), now)
