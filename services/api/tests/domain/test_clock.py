from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from tsuyulabo_api.domain.clock import (
    JST,
    completed_slots,
    game_day,
    iter_slots,
    next_slot_start,
    research_day,
    slot_of,
    weekday_label,
)


@pytest.mark.parametrize(
    "hour,minute,slot,day,next_hour",
    [
        (3, 59, "night", 26, 4),
        (4, 0, "morning", 27, 12),
        (11, 59, "morning", 27, 12),
        (12, 0, "noon", 27, 18),
        (17, 59, "noon", 27, 18),
        (18, 0, "night", 27, 4),
    ],
)
def test_boundaries(hour: int, minute: int, slot: str, day: int, next_hour: int) -> None:
    now = datetime(2026, 9, 27, hour, minute, tzinfo=JST)
    assert slot_of(now) == slot
    assert game_day(now).day == day
    assert next_slot_start(now).hour == next_hour
    assert next_slot_start(now) > now
    assert slot_of(now.astimezone(UTC)) == slot


def test_research_day_and_slots() -> None:
    start = datetime(2026, 9, 27, 10, tzinfo=JST)
    boundary = start.replace(hour=4) + timedelta(days=1)
    assert research_day(start, boundary - timedelta(microseconds=1)) == 1
    assert research_day(start, boundary) == 2
    assert weekday_label(1) == "月"
    assert weekday_label(7) == "日"
    assert len(list(iter_slots(start, boundary))) == 3
    assert len(list(completed_slots(start, boundary))) == 3
    assert list(iter_slots(start, start)) == []
    assert len(list(completed_slots(start, start.replace(hour=12)))) == 1
    with pytest.raises(ValueError):
        slot_of(datetime(2026, 9, 27))
    with pytest.raises(ValueError):
        list(iter_slots(boundary, start))
