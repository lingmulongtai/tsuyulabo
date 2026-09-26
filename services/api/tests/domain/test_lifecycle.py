from __future__ import annotations

from datetime import datetime

import pytest
from tsuyulabo_api.domain.clock import JST, research_day_start
from tsuyulabo_api.domain.events import CareEvent
from tsuyulabo_api.domain.lifecycle import action_availability, hatch_at, ready_to_eclose, stage_at

START = datetime(2026, 9, 27, 8, tzinfo=JST)


@pytest.mark.parametrize(
    "day,hour,stage",
    [
        (1, 8, "egg"),
        (1, 18, "larva1"),
        (2, 4, "larva1"),
        (3, 4, "larva2"),
        (4, 4, "larva3"),
        (5, 4, "wandering"),
        (6, 4, "pupa"),
        (7, 18, "pupa"),
        (20, 4, "pupa"),
    ],
)
def test_stages(day: int, hour: int, stage: str) -> None:
    now = research_day_start(START, day).replace(hour=hour)
    assert stage_at(START, now) == stage
    assert ready_to_eclose(START, now) == (day > 7 or day == 7 and hour >= 18)


def test_late_receipt_and_before_receipt() -> None:
    late = START.replace(hour=23)
    assert hatch_at(late) == late
    assert stage_at(late, late) == "larva1"
    with pytest.raises(ValueError):
        stage_at(late, START)


def test_daily_and_slot_quotas() -> None:
    now = research_day_start(START, 2)
    events = [CareEvent(now, "training")] * 3 + [CareEvent(now, "meal")]
    items = {t.action: t for t in action_availability(START, now, events)}
    assert items["training"].status == "done"
    assert items["training"].available_at == research_day_start(START, 3)
    assert items["meal"].status == "done"
    assert items["meal"].available_at == now.replace(hour=12)
    assert items["cleaning"].status == "available"
    assert items["temperature"].available_at == research_day_start(START, 6)
    assert items["sleep"].available_at == now.replace(hour=18)
    assert items["wake"].status == "available"
    items = {t.action: t for t in action_availability(START, now.replace(hour=12), events)}
    assert items["meal"].status == "available"
    assert items["training"].status == "done"


def test_site_and_expired_week() -> None:
    now = research_day_start(START, 5).replace(hour=18)
    assert (
        next(t for t in action_availability(START, now, []) if t.action == "pupation_site").status
        == "available"
    )
    items = action_availability(START, research_day_start(START, 9), [])
    assert all(t.status == "locked" and t.available_at is None for t in items[:5])
    assert items[-1].status == "available"
