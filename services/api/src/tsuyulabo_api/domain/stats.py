from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from . import constants as c
from .clock import local, research_day_start
from .lifecycle import hatch_at


def clamp(value: float) -> float:
    return max(0.0, min(c.STAT_MAX, value))


@dataclass(frozen=True)
class Stats:
    last_computed_at: datetime
    hunger: float = c.HATCH_HUNGER
    cleanliness: float = c.HATCH_CLEANLINESS
    hatched: bool = False
    hunger_zero_since: datetime | None = None
    starvation_at: datetime | None = None

    def display(self) -> dict[str, int | str]:
        return {
            "hunger": round(clamp(self.hunger)),
            "cleanliness": round(clamp(self.cleanliness)),
            "mood": mood(self.hunger, self.cleanliness),
            "mood_label": mood_label(mood(self.hunger, self.cleanliness)),
        }


def mood(hunger: float, cleanliness: float) -> int:
    return round(
        c.MOOD_HUNGER_WEIGHT * clamp(hunger) + c.MOOD_CLEANLINESS_WEIGHT * clamp(cleanliness)
    )


def mood_label(value: int) -> str:
    return next(label for threshold, label in c.MOOD_LABELS if clamp(value) >= threshold)


def decay(state: Stats, week_start: datetime, now: datetime) -> Stats:
    now, last = local(now), local(state.last_computed_at)
    if last < local(week_start) or now < last:
        raise ValueError("invalid stat interval")
    hatch = hatch_at(week_start)
    pupa = research_day_start(week_start, c.PUPA_DAY)
    if now < hatch:
        return replace(state, last_computed_at=now)
    if not state.hatched:
        state = Stats(last, hatched=True)
        last = hatch  # Initialize at hatch even when the caller skipped intermediate reads.
    begin, end = max(last, hatch), min(now, pupa)
    if begin < end:
        hours = (end - begin).total_seconds() / 3600
        hunger = clamp(state.hunger - c.HUNGER_DECAY * hours)
        zero = state.hunger_zero_since
        if hunger == 0 and zero is None:
            zero = begin + timedelta(hours=clamp(state.hunger) / c.HUNGER_DECAY)
        starvation = state.starvation_at
        if zero is not None and zero + timedelta(hours=c.HUNGER_ZERO_HOURS) <= end:
            starvation = starvation or zero + timedelta(hours=c.HUNGER_ZERO_HOURS)
        state = replace(
            state,
            hunger=hunger,
            cleanliness=clamp(state.cleanliness - c.CLEANLINESS_DECAY * hours),
            hunger_zero_since=zero,
            starvation_at=starvation,
        )
    return replace(
        state,
        last_computed_at=now,
        hunger_zero_since=None if now >= pupa else state.hunger_zero_since,
    )


def apply_meal(state: Stats, great_success: bool = False) -> Stats:
    """Apply after decay at the event timestamp."""
    gain = c.GREAT_MEAL_HUNGER if great_success else c.MEAL_HUNGER
    return replace(state, hunger=clamp(state.hunger + gain), hunger_zero_since=None)


def apply_cleaning(state: Stats, score: int) -> Stats:
    return replace(state, cleanliness=clamp(score))
