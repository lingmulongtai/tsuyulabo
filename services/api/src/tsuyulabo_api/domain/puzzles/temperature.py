from __future__ import annotations

from math import floor, pi, sin
from random import Random

from .. import constants as c
from .common import JsonObject, VerifyResult, times_reason


def generate(rng: Random, context: JsonObject) -> tuple[JsonObject, JsonObject]:
    return {
        "period_ms": c.TEMPERATURE_PERIOD_MS,
        "center_c": c.TEMPERATURE_CENTER_C,
        "amp_c": c.TEMPERATURE_AMP_C,
        "phase": rng.random(),
    }, {}


def temperature_at(params: JsonObject, stop_ms: int) -> float:
    return params["center_c"] + params["amp_c"] * sin(
        2 * pi * (stop_ms / params["period_ms"] + params["phase"])
    )


def verify(params: JsonObject, submission: JsonObject) -> VerifyResult:
    stop = submission.get("stop_ms")
    reason = times_reason([stop], submission.get("elapsed_ms"))
    if reason:
        return VerifyResult(False, reason)
    raw_score = (
        c.STAT_MAX
        - abs(temperature_at(params, stop) - c.TEMPERATURE_CENTER_C) * c.TEMPERATURE_PENALTY
    )
    # Match JavaScript Math.round for portable fixtures (positive half ties round up).
    score = max(0, floor(raw_score + 0.5))
    grade = next(label for threshold, label in c.TEMPERATURE_GRADES if score >= threshold)
    return VerifyResult(True, score=score, grade=grade)
