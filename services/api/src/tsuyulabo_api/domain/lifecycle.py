from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from . import constants as c
from .clock import local, next_slot_start, research_day, research_day_start, slot_of
from .events import CareEvent


def stage_at(week_start: datetime, now: datetime) -> str:
    if local(now) < local(week_start):
        raise ValueError("now precedes egg receipt")
    day = research_day(week_start, now)
    if day == c.HATCH_DAY and slot_of(now) != "night":
        return "egg"
    if day < c.MOLT_DAY:
        return "larva1"
    if day < c.LARVA3_DAY:
        return "larva2"
    if day < c.WANDERING_DAY:
        return "larva3"
    if day < c.PUPA_DAY:
        return "wandering"
    return "pupa"


def hatch_at(week_start: datetime) -> datetime:
    return max(
        local(week_start),
        research_day_start(week_start, c.HATCH_DAY).replace(hour=c.SLOT_HOURS["night"]),
    )


def ready_to_eclose(week_start: datetime, now: datetime) -> bool:
    return local(now) >= research_day_start(week_start, c.ECLOSION_DAY).replace(
        hour=c.SLOT_HOURS["night"]
    )


@dataclass(frozen=True)
class TodoItem:
    action: str
    status: Literal["done", "available", "locked"]
    available_at: datetime | None
    used: int
    limit: int


def _windows(week_start: datetime, action: str, now: datetime) -> list[tuple[datetime, datetime]]:
    days = {
        "meal": c.MEAL_DAYS,
        "training": c.TRAINING_DAYS,
        "cleaning": c.CLEANING_DAYS,
        "temperature": c.TEMPERATURE_DAYS,
        "pupation_site": (c.WANDERING_DAY,),
    }
    action_days = days.get(action, range(1, max(c.WEEK_DAYS, research_day(week_start, now)) + 2))
    windows = []
    for day in action_days:
        start = research_day_start(week_start, day)
        if action == "meal":
            for hour in c.SLOT_HOURS.values():
                begin = start.replace(hour=hour)
                windows.append((max(begin, local(week_start)), next_slot_start(begin)))
        elif action in ("sleep", "wake", "pupation_site"):
            begin = start.replace(hour=c.SLOT_HOURS["morning" if action == "wake" else "night"])
            windows.append((max(begin, local(week_start)), next_slot_start(begin)))
        else:
            windows.append((max(start, local(week_start)), start + timedelta(days=1)))
    return [(a, b) for a, b in windows if a < b]


def action_availability(
    week_start: datetime, now: datetime, usage: Iterable[CareEvent]
) -> list[TodoItem]:
    """Return each action's current quota and earliest next usable window.

    Usage is the successful event log for this week. At quota, status is done;
    outside a window, locked. Expired weekly actions have no available_at.
    """
    now = local(now)
    events = tuple(usage)
    result = []
    for action in ("meal", "training", "cleaning", "temperature", "pupation_site", "sleep", "wake"):
        limit = c.TRAINING_DAILY_LIMIT if action == "training" else c.ONCE
        item = TodoItem(action, "locked", None, 0, limit)
        for start, end in _windows(week_start, action, now):
            used = sum(e.kind == action and start <= local(e.at) < end for e in events)
            if start <= now < end:
                item = TodoItem(
                    action,
                    "done" if used >= limit else "available",
                    now if used < limit else None,
                    used,
                    limit,
                )
                if used < limit:
                    break
            elif start > now and used < limit:
                item = TodoItem(action, item.status, start, item.used, limit)
                break
        result.append(item)
    return result
