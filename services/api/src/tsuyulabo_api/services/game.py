"""Shared transaction helpers. Lock the owning user before evaluating game state."""

from __future__ import annotations

from datetime import datetime
from random import Random
from secrets import randbits
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.auth.dependencies import get_current_user
from tsuyulabo_api.brain_adapter import BrainAdapter, get_brain
from tsuyulabo_api.db.models import CareEvent, User
from tsuyulabo_api.db.session import get_session
from tsuyulabo_api.domain.clock import research_day, slot_of
from tsuyulabo_api.services.clock import Clock, get_clock
from tsuyulabo_api.services.ledger import get_account, transfer

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentClock = Annotated[Clock, Depends(get_clock)]
Brain = Annotated[BrainAdapter, Depends(get_brain)]


async def locked_user(user: Annotated[User, Depends(get_current_user)], session: Session) -> User:
    return await session.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


CurrentUser = Annotated[User, Depends(locked_user)]


def rng() -> Random:
    return Random(randbits(128))


async def reward(
    session: AsyncSession, user_id: str, currency: str, amount: int, reason: str, ref: str
) -> None:
    if not amount:
        return
    source = await get_account(session, "system:rewards", currency)
    target = await get_account(session, f"user:{user_id}", currency)
    if amount < 0:
        source, target = target, source
    await transfer(session, source, target, abs(amount), reason, ref)


async def record_care(
    session: AsyncSession,
    user_id: str,
    week_id: str,
    started_at: datetime,
    now: datetime,
    kind: str,
    payload: dict[str, Any],
) -> CareEvent:
    seq = (
        await session.scalar(select(func.max(CareEvent.seq)).where(CareEvent.user_id == user_id))
        or 0
    ) + 1
    event = CareEvent(
        user_id=user_id,
        week_id=week_id,
        seq=seq,
        kind=kind,
        research_day=research_day(started_at, now),
        slot=slot_of(now),
        score=payload.get("score"),
        payload=payload,
        created_at=now,
    )
    session.add(event)
    await session.flush()
    return event
