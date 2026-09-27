from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.models import ShioriMessage
from tsuyulabo_api.domain.clock import day_start, game_day


async def today(session: AsyncSession, user_id: str, now: datetime) -> dict[str, Any] | None:
    start = day_start(game_day(now))
    memo = await session.scalar(
        select(ShioriMessage)
        .where(
            ShioriMessage.user_id == user_id,
            ShioriMessage.role == "memo",
            ShioriMessage.created_at >= start,
            ShioriMessage.created_at < start + timedelta(days=1),
        )
        .order_by(ShioriMessage.created_at.desc())
        .limit(1)
    )
    return {"id": memo.id, "text": memo.text, "evidence": memo.evidence} if memo else None
