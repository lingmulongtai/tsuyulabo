from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from tsuyulabo_api.domain.clock import JST
from tsuyulabo_api.domain.sleep import energy_recovery, sleep_bonus, sleep_duration, wake


def test_sleep_caps_and_recovery() -> None:
    start = datetime(2026, 9, 27, 22, tzinfo=JST)
    result = wake(start, start + timedelta(hours=8), 10)
    assert (result.hours, result.shizuku, result.energy) == (8, 200, 100)
    assert sleep_duration(start, start + timedelta(hours=20)) == 10
    assert sleep_bonus(1.5) == 37
    assert sleep_bonus(10) == 200
    assert energy_recovery(2, 0.2) == 36
    assert energy_recovery(10) == 100
    early = start.replace(hour=3)
    assert wake(early, early.replace(hour=4), 5).energy == 20
    with pytest.raises(ValueError):
        sleep_duration(start, start - timedelta(seconds=1))
    with pytest.raises(ValueError):
        wake(start.replace(hour=12), start + timedelta(hours=8), 10)
