from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from tsuyulabo_api.db.models import SleepSession, Week
from tsuyulabo_api.domain import adults, sleep
from tsuyulabo_api.domain.clock import game_day, slot_of
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services import team
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import (
    Brain,
    CurrentClock,
    CurrentUser,
    Session,
    record_care,
    reward,
)
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/sleep", route_class=IdempotentRoute)


async def log_sleep(
    session: Session, user: CurrentUser, now: Any, kind: str, payload: dict
) -> None:
    week = await session.scalar(
        select(Week).where(Week.user_id == user.id, Week.status == "active")
    )
    if week is not None:
        await record_care(session, user.id, week.id, week.started_at, now, kind, payload)


@router.post("/start")
async def start(user: CurrentUser, session: Session, clock: CurrentClock) -> dict[str, Any]:
    now = game_now(clock, user)
    if slot_of(now) != "night":
        raise APIError("not_available_today", "おやすみは夜にできます", 409)
    sleeps = list(
        await session.scalars(select(SleepSession).where(SleepSession.user_id == user.id))
    )
    if any(game_day(s.started_at) == game_day(now) for s in sleeps):
        raise APIError("daily_limit_reached", "今日はおやすみ済みです", 409)
    if any(s.ended_at is None for s in sleeps):
        raise APIError("sleep_already_active", "先におはようをしてください", 409)
    record = SleepSession(user_id=user.id, started_at=now)
    session.add(record)
    await session.flush()
    await log_sleep(session, user, now, "sleep", {"sleep_id": record.id})
    return {"id": record.id, "started_at": now}


@router.post("/end")
async def end(
    user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    now = game_now(clock, user)
    if slot_of(now) != "morning":
        raise APIError("not_available_today", "おはようは朝にできます", 409)
    sleeps = list(
        await session.scalars(select(SleepSession).where(SleepSession.user_id == user.id))
    )
    if any(s.ended_at and game_day(s.ended_at) == game_day(now) for s in sleeps):
        raise APIError("daily_limit_reached", "今日はおはよう済みです", 409)
    record = next((s for s in sleeps if s.ended_at is None), None)
    if record is None:
        raise APIError("no_active_sleep", "睡眠の記録がありません", 409)
    if now < record.started_at:
        raise APIError("time_reversed", "睡眠開始後に時刻を進めてください", 409)
    members = await team.settle(session, user.id, now, brain)
    hours = sleep.sleep_duration(record.started_at, now)
    recovered = {}
    for _, adult in members:
        result = sleep.wake(
            record.started_at, now, adult.energy, adults.bonuses(adult.subskills)["energy_bonus"]
        )
        recovered[adult.id] = result.energy - adult.energy
        adult.energy = result.energy
    record.ended_at, record.bonus = now, sleep.sleep_bonus(hours)
    await reward(session, user.id, "shizuku", record.bonus, "sleep", record.id)
    result = {"id": record.id, "hours": hours, "bonus": record.bonus, "energy_recovered": recovered}
    await log_sleep(session, user, now, "wake", result)
    return result
