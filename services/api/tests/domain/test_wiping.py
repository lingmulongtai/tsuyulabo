from __future__ import annotations

import pytest
from tsuyulabo_api.domain.puzzles import wiping


def strokes() -> list[dict]:
    return [
        {"u": (col + 0.5) / 6, "v": (row + 0.5) / 9, "t": (row * 6 + col) * 40}
        for row in range(9)
        for col in range(6)
    ]


def test_wiping_coverage_time_and_existing_reward_grades() -> None:
    body = {"strokes": strokes(), "elapsed_ms": 2200}
    result = wiping.verify(body)
    assert result.valid and result.score == 100 and result.grades == ("perfect",) * 3
    assert wiping.verify(body | {"elapsed_ms": 8000}).score == 66
    assert wiping.verify({"strokes": strokes()[:2], "elapsed_ms": 100}).score == 15


@pytest.mark.parametrize(
    "change", [{"u": float("nan")}, {"v": 1.1}, {"u": True}, {"t": -1}, {"t": 10001}]
)
def test_wiping_rejects_forged_stamps(change: dict) -> None:
    points = strokes()
    points[0] |= change
    assert not wiping.verify({"strokes": points, "elapsed_ms": 2200}).valid
