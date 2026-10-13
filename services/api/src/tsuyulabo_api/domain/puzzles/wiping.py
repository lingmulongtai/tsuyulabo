"""Validate glass UV strokes and reuse cleaning's three-zone reward grades."""

from __future__ import annotations

from math import hypot, isfinite

from .. import constants as c
from .common import JsonObject, VerifyResult, times_reason

ROWS, COLS, RADIUS = 18, 12, 0.12


def verify(submission: JsonObject) -> VerifyResult:
    strokes = submission.get("strokes")
    if not isinstance(strokes, list) or not 2 <= len(strokes) <= 800:
        return VerifyResult(False, "wrong_length")
    if any(not isinstance(p, dict) for p in strokes):
        return VerifyResult(False, "wrong_length")
    reason = times_reason(
        [p.get("t") for p in strokes],
        submission.get("elapsed_ms"),
        strict=True,
        limit=c.CLEANING_TIME_LIMIT_MS,
    )
    if reason:
        return VerifyResult(False, reason)
    if submission["elapsed_ms"] > c.CLEANING_TIME_LIMIT_MS:
        return VerifyResult(False, "time_exceeded")
    mask: set[tuple[int, int]] = set()
    previous = None
    for p in strokes:
        u, v = p.get("u"), p.get("v")
        if any(type(n) not in (int, float) or not isfinite(n) or not 0 <= n <= 1 for n in (u, v)):
            return VerifyResult(False, "out_of_bounds")
        # Each sample is a brush stamp; jumps between strokes do not erase a line.
        if previous is not None and p["t"] - previous["t"] < 12:
            return VerifyResult(False, "non_monotonic_time")
        previous = p
        for row in range(ROWS):
            for col in range(COLS):
                if hypot((col + 0.5) / COLS - u, (row + 0.5) / ROWS - v) <= RADIUS:
                    mask.add((row, col))
    grades = []
    for zone in range(3):
        coverage = sum(row // 6 == zone for row, _ in mask) / (6 * COLS)
        grades.append(
            "perfect"
            if coverage >= 0.75 and submission["elapsed_ms"] <= 7000
            else "good"
            if coverage >= 0.45
            else "miss"
        )
    return VerifyResult(
        True, score=min(100, sum(c.CLEANING_POINTS[g] for g in grades)), grades=tuple(grades)
    )
