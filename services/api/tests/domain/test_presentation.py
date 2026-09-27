from __future__ import annotations

from datetime import UTC, datetime

import pytest
from tsuyulabo_api.domain.events import CareEvent
from tsuyulabo_api.domain.presentation import rank_for, rewards, summarize


@pytest.mark.parametrize(
    "points,rank",
    [
        (-500, "normal"),
        (24999, "normal"),
        (25000, "silver"),
        (44999, "silver"),
        (45000, "gold"),
        (69999, "gold"),
        (70000, "rainbow"),
    ],
)
def test_ranks(points: int, rank: str) -> None:
    assert rank_for(points) == rank


def test_breakdown_and_rewards() -> None:
    at = datetime(2026, 1, 1, tzinfo=UTC)
    events = [
        CareEvent(at, "meal", 2000, great_success=True),
        CareEvent(at, "training", stars=3, hirameki=True),
        CareEvent(at, "cleaning", 80),
        CareEvent(at, "temperature", 100),
        CareEvent(at, "pupation_site", hit=True),
    ]
    result = summarize(events, [("meal", 2, "night")] * 2)
    assert (result.meal_points, result.training_points, result.care_points) == (3000, 1500, 1900)
    assert result.points == 5900 and result.care_miss == 1
    assert (result.shizuku, result.research_points) == (983, 147)
    assert rewards(4000, 0.05) == (666, 105)
    assert rewards(-1) == (0, 0)
    assert rewards(-9000, 0.1) == (0, 0)
