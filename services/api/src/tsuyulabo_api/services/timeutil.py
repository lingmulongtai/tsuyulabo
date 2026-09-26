"""Temporary JST helpers; replace with domain.clock during W2 integration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

JST = timezone(timedelta(hours=9), name="Asia/Tokyo")


def slot_at(now: datetime) -> str:
    hour = now.astimezone(JST).hour
    return "morning" if 4 <= hour < 12 else "noon" if 12 <= hour < 18 else "night"


def next_boundary(now: datetime, target: Literal["next_slot", "next_day"]) -> datetime:
    local = now.astimezone(JST)
    hours = (4,) if target == "next_day" else (4, 12, 18)
    candidates = [
        (local + timedelta(days=day)).replace(hour=hour, minute=0, second=0, microsecond=0)
        for day in (0, 1)
        for hour in hours
    ]
    return min(candidate for candidate in candidates if candidate > local)
