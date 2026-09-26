from __future__ import annotations

from random import Random

from .. import constants as c
from .common import JsonObject, VerifyResult, times_reason


def generate(rng: Random, context: JsonObject) -> tuple[JsonObject, JsonObject]:
    day = context.get("research_day", 2)
    if day not in c.CLEANING_PERIODS:
        raise ValueError("cleaning requires research day 2 through 5")
    return {
        "period_ms": c.CLEANING_PERIODS[day],
        "taps": c.CLEANING_TAPS,
        "zone": dict(c.CLEANING_ZONE),
        "phase": rng.random(),
    }, {}


def position(t: int, period_ms: int, phase: float) -> float:
    u = (t / period_ms + phase) % 1
    return 2 * u if u < 0.5 else 2 - 2 * u


def verify(params: JsonObject, submission: JsonObject) -> VerifyResult:
    taps = submission.get("taps")
    if not isinstance(taps, list) or len(taps) != params["taps"]:
        return VerifyResult(False, "wrong_tap_count")
    reason = times_reason(
        taps, submission.get("elapsed_ms"), strict=True, limit=c.CLEANING_TIME_LIMIT_MS
    )
    if reason:
        return VerifyResult(False, reason)
    grades = []
    for t in taps:
        distance = abs(position(t, params["period_ms"], params["phase"]) - params["zone"]["center"])
        grade = (
            "perfect"
            if distance <= params["zone"]["perfect"] + 1e-12
            else ("good" if distance <= params["zone"]["good"] + 1e-12 else "miss")
        )
        grades.append(grade)
    return VerifyResult(
        True, score=min(c.STAT_MAX, sum(c.CLEANING_POINTS[g] for g in grades)), grades=tuple(grades)
    )
