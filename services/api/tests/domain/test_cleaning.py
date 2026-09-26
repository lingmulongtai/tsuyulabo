from __future__ import annotations

from random import Random

import pytest
from tsuyulabo_api.domain.puzzles import cleaning


@pytest.mark.parametrize("day,period", [(2, 1400), (3, 1300), (4, 1200), (5, 1100)])
def test_generation(day: int, period: int) -> None:
    p, secret = cleaning.generate(Random(1), {"research_day": day})
    assert p["period_ms"] == period and not secret
    assert 0 <= p["phase"] < 1


def test_grades_timing_and_triangle() -> None:
    p, _ = cleaning.generate(Random(1), {})
    p.update(period_ms=1000, phase=0)
    assert cleaning.verify(p, {"taps": [250, 750, 1250], "elapsed_ms": 1250}).score == 100
    result = cleaning.verify(p, {"taps": [250, 800, 1000], "elapsed_ms": 1000})
    assert result.score == 61 and result.grades == ("perfect", "good", "miss")
    assert cleaning.position(0, 1000, 0) == 0
    assert cleaning.position(500, 1000, 0) == 1
    assert cleaning.position(1000, 1000, 0) == 0
    for taps, elapsed, reason in [
        ([1, 2], 2, "wrong_tap_count"),
        ([1, 1, 2], 2, "non_monotonic_time"),
        ([3, 2, 4], 4, "non_monotonic_time"),
        ([1, 2, 10001], 10001, "time_exceeded"),
    ]:
        assert cleaning.verify(p, {"taps": taps, "elapsed_ms": elapsed}).reason == reason
    assert cleaning.verify(p, {"taps": [1, 2, 10000], "elapsed_ms": 10000}).valid


@pytest.mark.parametrize(
    "taps,grade",
    [
        ([220, 280, 780], "perfect"),
        ([175, 325, 825], "good"),
        ([219, 281, 781], "good"),
        ([174, 326, 826], "miss"),
    ],
)
def test_inclusive_zone_edges(taps: list[int], grade: str) -> None:
    p, _ = cleaning.generate(Random(1), {})
    p.update(period_ms=1000, phase=0)
    assert cleaning.verify(p, {"taps": taps, "elapsed_ms": taps[-1]}).grades == (grade,) * 3
