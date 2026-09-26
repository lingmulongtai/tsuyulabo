from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from . import constants as c
from .clock import completed_slots, local, research_day, research_day_start
from .events import CareEvent
from .stats import Stats, apply_cleaning, apply_meal, decay

type MissKey = tuple[str, int, str | None]


def evaluate(
    week_start: datetime, start: datetime, now: datetime, events: Iterable[CareEvent]
) -> set[MissKey]:
    """Misses whose deadlines are in (start, now], keyed within one research week.

    Pass the complete successful care log since egg receipt, including events
    before start. Union the returned set with stored keys for idempotency.
    Starvation is charged once per week, at the first three-hour zero interval.
    """
    start, now = local(start), local(now)
    if start < local(week_start) or now < start:
        raise ValueError("invalid evaluation interval")
    log = sorted(
        (e for e in events if local(week_start) <= local(e.at) <= now), key=lambda e: local(e.at)
    )
    misses: set[MissKey] = set()

    def did(kind: str, begin: datetime, end: datetime) -> bool:
        return any(e.kind == kind and begin <= local(e.at) < end for e in log)

    for slot in completed_slots(start, now):
        day = research_day(week_start, slot.start)
        if day in c.CLEANING_DAYS and not did("meal", slot.start, slot.end):
            misses.add(("meal", day, slot.slot))
    for day in range(1, c.PUPA_DAY + 1):
        begin = research_day_start(week_start, day)
        end = begin + timedelta(days=1)
        if not start < end <= now:
            continue
        required = []
        if day in c.CLEANING_DAYS:
            required.append("cleaning")
        if day in c.TEMPERATURE_DAYS:
            required.append("temperature")
        if day == c.WANDERING_DAY:
            required.append("pupation_site")
        for kind in required:
            action_begin = (
                begin.replace(hour=c.SLOT_HOURS["night"]) if kind == "pupation_site" else begin
            )
            if not did(kind, max(action_begin, local(week_start)), end):
                misses.add((kind, day, None))
    state = Stats(local(week_start))
    for event in log:
        state = decay(state, week_start, local(event.at))
        if event.kind == "meal":
            state = apply_meal(state, event.great_success)
        elif event.kind == "cleaning":
            state = apply_cleaning(state, event.score)
    state = decay(state, week_start, now)
    if state.starvation_at is not None and start < state.starvation_at <= now:
        misses.add(("hunger_zero", research_day(week_start, state.starvation_at), None))
    return misses


def default_pupation_choice(options: list[dict[str, str]]) -> str:
    """The API applies the middle choice when the site action's deadline passes."""
    if not options:
        raise ValueError("site options must not be empty")
    return options[len(options) // 2]["id"]
