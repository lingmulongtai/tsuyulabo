from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from tsuyulabo_api.db.models import Week
from tsuyulabo_api.domain import lifecycle
from tsuyulabo_api.domain.clock import research_day, research_day_start, slot_of, weekday_label
from tsuyulabo_api.domain.constants import SLOT_HOURS
from tsuyulabo_api.services import memo, team
from tsuyulabo_api.services import week as service
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import Brain, CurrentClock, CurrentUser, Session
from tsuyulabo_api.services.ledger import balances

router = APIRouter(prefix="/v1/home")


@router.get("")
async def home(
    user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    now = game_now(clock, user)
    week = await session.scalar(
        select(Week).where(Week.user_id == user.id, Week.status == "active")
    )
    result = {
        "clock": {
            "game_now": now,
            "slot": slot_of(now),
            "research_day": None,
            "weekday_label": None,
        },
        "week": None,
        "fly": None,
        "todo": [],
        "balances": await balances(session, user.id),
        "team": team.payload(await team.settle(session, user.id, now, brain)),
        "shiori": {"memo": await memo.today(session, user.id, now)},
    }
    if week is not None:
        day = research_day(week.started_at, now)
        detail = await service.payload(session, week, now)
        result["clock"].update(research_day=day, weekday_label=weekday_label(day))
        result["week"] = {
            key: detail[key]
            for key in (
                "id",
                "research_day",
                "stage",
                "ready_to_eclose",
                "care_miss",
                "points_so_far",
            )
        }
        result["fly"] = detail["fly"]
        usage = service.domain_events(await service.events(session, week))
        for item in lifecycle.action_availability(week.started_at, now, usage):
            todo = asdict(item)
            todo["remaining"] = max(0, item.limit - item.used)
            if item.action == "meal":
                todo["slot"] = slot_of(now)
            result["todo"].append(todo)
        if day <= 7:
            for slot, hour in SLOT_HOURS.items():
                available_at = research_day_start(week.started_at, day).replace(hour=hour)
                if available_at > now:
                    result["todo"].append(
                        {
                            "action": "meal",
                            "status": "locked",
                            "slot": slot,
                            "available_at": available_at,
                        }
                    )
    return result
