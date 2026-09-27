"""Clock-time regularity derived from completed sleep records (game-rules §10b)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from math import atan2, cos, floor, hypot, inf, log, pi, sin, sqrt

from . import constants as c
from .clock import game_day, local


@dataclass(frozen=True)
class SleepRecord:
    started_at: datetime
    ended_at: datetime | None


@dataclass(frozen=True)
class Circadian:
    gauge: int = 0
    streak: int = 0
    typical_bedtime: str | None = None
    typical_wake: str | None = None

    @property
    def energy_multiplier(self) -> float:
        return 1 + c.CIRCADIAN_MAX_ENERGY_BONUS * self.gauge / 100

    @property
    def shizuku_bonus(self) -> int:
        return c.CIRCADIAN_SHIZUKU_BONUS if self.gauge >= c.CIRCADIAN_BONUS_THRESHOLD else 0


def clock_statistics(times: Iterable[datetime]) -> tuple[float, str | None]:
    """Return circular standard deviation in minutes and rounded circular mean."""
    angles = []
    for time in times:
        time = local(time)
        minutes = time.hour * 60 + time.minute + time.second / 60 + time.microsecond / 60e6
        angles.append(2 * pi * minutes / 1440)
    if not angles:
        return inf, None
    x = sum(cos(angle) for angle in angles) / len(angles)
    y = sum(sin(angle) for angle in angles) / len(angles)
    radius = min(1, hypot(x, y))
    if radius <= 1e-12:
        return inf, None
    deviation = sqrt(-2 * log(radius)) * 1440 / (2 * pi)
    minute = floor((atan2(y, x) % (2 * pi)) * 1440 / (2 * pi) + 0.5) % 1440
    return deviation, f"{minute // 60:02d}:{minute % 60:02d}"


def summarize(records: Iterable[SleepRecord], now: datetime) -> Circadian:
    now = local(now)
    completed = []
    for record in records:
        start = local(record.started_at)
        end = local(record.ended_at) if record.ended_at is not None else None
        if end is not None and start <= end <= now:
            completed.append((start, end))
    completed.sort(key=lambda pair: (pair[1], pair[0]), reverse=True)
    completed = completed[: c.CIRCADIAN_WINDOW]
    if not completed:
        return Circadian()
    bed_spread, bedtime = clock_statistics(start for start, _ in completed)
    wake_spread, waketime = clock_statistics(end for _, end in completed)
    durations = [
        c.CIRCADIAN_MIN_HOURS <= (end - start).total_seconds() / 3600 <= c.CIRCADIAN_MAX_HOURS
        for start, end in completed
    ]
    score = sum(
        c.CIRCADIAN_REGULARITY_POINTS * max(0, 1 - spread / c.CIRCADIAN_SPREAD_MINUTES)
        for spread in (bed_spread, wake_spread)
    ) + c.CIRCADIAN_DURATION_POINTS * sum(durations) / len(completed)
    gauge = min(100, max(0, floor(score * len(completed) / c.CIRCADIAN_WINDOW + 0.5)))
    streak = 0
    if (game_day(now) - game_day(completed[0][1])).days <= 1:
        previous = None
        for (start, _), good_duration in zip(completed, durations, strict=True):
            day = game_day(start)
            if not good_duration or (previous is not None and (previous - day).days != 1):
                break
            streak += 1
            previous = day
    return Circadian(gauge, streak, bedtime, waketime)
