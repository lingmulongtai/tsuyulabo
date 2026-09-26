from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from ..constants import PUZZLE_EXPIRY_MS, WALL_CLOCK_GRACE_MS

type JsonObject = dict[str, Any]


@dataclass(frozen=True)
class VerifyResult:
    valid: bool
    reason: str | None = None
    score: int | None = None
    lines: int | None = None
    max_combo: int | None = None
    theme_cells: int | None = None
    stars: int | None = None
    grades: tuple[str, ...] | None = None
    grade: str | None = None

    def to_dict(self) -> JsonObject:
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in asdict(self).items()
            if value is not None
        }


def integer(value: object) -> bool:
    return type(value) is int


def times_reason(
    times: list[Any], elapsed: Any, *, strict: bool = False, limit: int = PUZZLE_EXPIRY_MS
) -> str | None:
    if not integer(elapsed) or elapsed < 0:
        return "non_monotonic_time"
    if elapsed > PUZZLE_EXPIRY_MS:
        return "time_exceeded"
    previous = -1
    for value in times:
        if not integer(value) or value < 0 or value < previous or (strict and value == previous):
            return "non_monotonic_time"
        if value > limit:
            return "time_exceeded"
        previous = value
    if previous > elapsed:
        return "non_monotonic_time"
    return None


def verify_wall_clock(issued_at: datetime, submitted_at: datetime, last_t: int) -> VerifyResult:
    from ..clock import local

    elapsed = (local(submitted_at) - local(issued_at)).total_seconds() * 1000
    if elapsed < 0 or not integer(last_t) or last_t < 0:
        return VerifyResult(False, "non_monotonic_time")
    if elapsed >= PUZZLE_EXPIRY_MS or elapsed < last_t - WALL_CLOCK_GRACE_MS:
        return VerifyResult(False, "time_exceeded")
    return VerifyResult(True)
