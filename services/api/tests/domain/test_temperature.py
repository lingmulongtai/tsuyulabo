from __future__ import annotations

from random import Random

import pytest
from tsuyulabo_api.domain.puzzles import temperature


def test_wave_and_rounding() -> None:
    params, secret = temperature.generate(Random(1), {})
    params["phase"] = 0
    assert not secret
    for stop, score in [(0, 100), (400, 0), (800, 100), (1200, 0), (1600, 100)]:
        assert temperature.verify(params, {"stop_ms": stop, "elapsed_ms": stop}).score == score
    params.update(amp_c=0, center_c=25.125)
    assert temperature.verify(params, {"stop_ms": 0, "elapsed_ms": 0}).score == 98


@pytest.mark.parametrize(
    "center,score,grade",
    [(25.5, 90, "perfect"), (25.55, 89, "good"), (27, 60, "good"), (27.05, 59, "miss")],
)
def test_grade_boundaries(center: float, score: int, grade: str) -> None:
    params, _ = temperature.generate(Random(1), {})
    params.update(amp_c=0, center_c=center)
    result = temperature.verify(params, {"stop_ms": 0, "elapsed_ms": 0})
    assert result.score == score and result.grade == grade


def test_invalid_times() -> None:
    params, _ = temperature.generate(Random(1), {})
    for stop, elapsed, reason in [
        (-1, 0, "non_monotonic_time"),
        (10, 9, "non_monotonic_time"),
        (600001, 600001, "time_exceeded"),
    ]:
        assert temperature.verify(params, {"stop_ms": stop, "elapsed_ms": elapsed}).reason == reason
