from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import floor

from . import constants as c
from .clock import local, slot_of


def sleep_duration(slept_at: datetime, woke_at: datetime) -> float:
    hours = (local(woke_at) - local(slept_at)).total_seconds() / 3600
    if hours < 0:
        raise ValueError("wake precedes sleep")
    return min(c.SLEEP_MAX_HOURS, hours)


def sleep_bonus(hours: float) -> int:
    if hours < 0:
        raise ValueError("negative duration")
    return floor(min(hours, c.SLEEP_BONUS_MAX_HOURS) * c.SLEEP_SHIZUKU_PER_HOUR)


def energy_recovery(hours: float, energy_up: float = 0) -> float:
    if hours < 0 or energy_up < 0:
        raise ValueError("negative duration or bonus")
    return min(
        c.STAT_MAX, min(hours, c.SLEEP_MAX_HOURS) * c.SLEEP_ENERGY_PER_HOUR * (1 + energy_up)
    )


@dataclass(frozen=True)
class SleepResult:
    hours: float
    shizuku: int
    energy_recovered: float
    energy: float


def wake(slept_at: datetime, woke_at: datetime, energy: float, energy_up: float = 0) -> SleepResult:
    """Pass the member's energy after gathering has been settled to woke_at."""
    if slot_of(slept_at) != "night" or slot_of(woke_at) != "morning":
        raise ValueError("sleep requires night and wake requires morning")
    if not 0 <= energy <= c.STAT_MAX:
        raise ValueError("invalid energy")
    hours = sleep_duration(slept_at, woke_at)
    recovery = energy_recovery(hours, energy_up)
    return SleepResult(hours, sleep_bonus(hours), recovery, min(c.STAT_MAX, energy + recovery))
