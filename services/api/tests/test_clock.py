from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from tsuyulabo_api.db.users import User
from tsuyulabo_api.services.clock import clock_payload
from tsuyulabo_api.services.timeutil import JST, next_boundary, slot_at


@pytest.mark.parametrize(
    ("hour", "slot", "next_hour"),
    [
        (3, "night", 4),
        (4, "morning", 12),
        (11, "morning", 12),
        (12, "noon", 18),
        (17, "noon", 18),
        (18, "night", 4),
        (23, "night", 4),
    ],
)
def test_slot_boundaries(hour: int, slot: str, next_hour: int) -> None:
    now = datetime(2026, 1, 2, hour, tzinfo=JST)
    assert slot_at(now) == slot
    assert next_boundary(now, "next_slot").hour == next_hour
    next_day = next_boundary(now, "next_day")
    assert next_day.hour == 4 and next_day > now
    assert next_day.date() == (now + timedelta(days=int(hour >= 4))).date()


def test_frozen_clock() -> None:
    class FrozenClock:
        def now(self) -> datetime:
            return datetime(2026, 1, 1, 18, tzinfo=UTC)

    user = User(dev_time_offset_s=3600)
    payload = clock_payload(FrozenClock(), user)
    assert payload == {
        "server_now": "2026-01-01T18:00:00+00:00",
        "game_now": "2026-01-01T19:00:00+00:00",
        "tz": "Asia/Tokyo",
        "slot": "morning",
        "day_boundary_hour": 4,
    }
