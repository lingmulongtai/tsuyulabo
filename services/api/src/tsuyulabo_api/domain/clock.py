"""Aware timestamps only; intervals are half-open [start, end)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .constants import DAY_BOUNDARY_HOUR, SLOT_HOURS, TIMEZONE, WEEKDAY_LABELS

try:
    JST = ZoneInfo(TIMEZONE)
except ZoneInfoNotFoundError:  # Windows may have no system IANA database; alpha JST is fixed.
    JST = timezone(timedelta(hours=9), TIMEZONE)


def local(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return dt.astimezone(JST)


def game_day(dt: datetime) -> date:
    return (local(dt) - timedelta(hours=DAY_BOUNDARY_HOUR)).date()


def slot_of(dt: datetime) -> str:
    hour = local(dt).hour
    if SLOT_HOURS["morning"] <= hour < SLOT_HOURS["noon"]:
        return "morning"
    if SLOT_HOURS["noon"] <= hour < SLOT_HOURS["night"]:
        return "noon"
    return "night"


def day_start(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, DAY_BOUNDARY_HOUR, tzinfo=JST)


def research_day(week_start: datetime, now: datetime) -> int:
    return (game_day(now) - game_day(week_start)).days + 1


def weekday_label(day: int) -> str:
    if day < 1:
        raise ValueError("research day must be positive")
    return WEEKDAY_LABELS[(day - 1) % len(WEEKDAY_LABELS)]


def research_day_start(week_start: datetime, day: int) -> datetime:
    return day_start(game_day(week_start) + timedelta(days=day - 1))


def slot_start(dt: datetime) -> datetime:
    return day_start(game_day(dt)).replace(hour=SLOT_HOURS[slot_of(dt)])


def next_slot_start(dt: datetime) -> datetime:
    start = slot_start(dt)
    slot = slot_of(dt)
    if slot == "night":
        return (start + timedelta(days=1)).replace(hour=DAY_BOUNDARY_HOUR)
    return start.replace(hour=SLOT_HOURS["noon" if slot == "morning" else "night"])


@dataclass(frozen=True)
class SlotInterval:
    day: date
    slot: str
    start: datetime
    end: datetime


def iter_slots(start: datetime, end: datetime) -> Iterator[SlotInterval]:
    """Yield full slot boundaries for slots intersecting [start, end)."""
    start, end = local(start), local(end)
    if end < start:
        raise ValueError("end precedes start")
    cursor = slot_start(start)
    while start < end and cursor < end:
        boundary = next_slot_start(cursor)
        yield SlotInterval(game_day(cursor), slot_of(cursor), cursor, boundary)
        cursor = boundary


def completed_slots(start: datetime, end: datetime) -> Iterator[SlotInterval]:
    """Yield slots with end boundaries in (start, end]."""
    for interval in iter_slots(start, end):
        if interval.end <= end:
            yield interval
