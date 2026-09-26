from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from tsuyulabo_api.domain.clock import JST, research_day_start
from tsuyulabo_api.domain.stats import Stats, apply_cleaning, apply_meal, decay, mood, mood_label

START = datetime(2026, 9, 27, 8, tzinfo=JST)
HATCH = START.replace(hour=18)


def test_hatch_decay_and_freeze() -> None:
    initial = Stats(START, hunger=10, cleanliness=20)
    assert decay(initial, START, START.replace(hour=17)).hunger == 10
    hatched = decay(initial, START, HATCH)
    assert (hatched.hunger, hatched.cleanliness) == (60, 100)
    state = decay(hatched, START, HATCH + timedelta(hours=2))
    assert state.hunger == 35
    assert state.cleanliness == 92
    assert state.display()["mood"] == 58
    before_pupa = research_day_start(START, 6) - timedelta(hours=1)
    state = Stats(before_pupa, 100, 100, True)
    frozen = decay(state, START, research_day_start(START, 8))
    assert (frozen.hunger, frozen.cleanliness) == (87.5, 96)
    assert decay(frozen, START, research_day_start(START, 20)).hunger == 87.5


def test_incremental_equals_single_read_and_starvation() -> None:
    initial = Stats(START)
    end = HATCH + timedelta(hours=8)
    once = decay(initial, START, end)
    split = decay(decay(initial, START, HATCH + timedelta(hours=5)), START, end)
    assert once == split
    assert once.hunger_zero_since == HATCH + timedelta(hours=4.8)
    assert once.starvation_at == HATCH + timedelta(hours=7.8)
    fed = apply_meal(once)
    assert fed.hunger == 40 and fed.hunger_zero_since is None
    assert fed.starvation_at == once.starvation_at
    assert apply_meal(fed, True).hunger == 100
    assert apply_cleaning(fed, 22).cleanliness == 22
    assert initial.hunger == 60


@pytest.mark.parametrize(
    "value,label",
    [
        (100, "ごきげん"),
        (70, "ごきげん"),
        (69, "ふつう"),
        (40, "ふつう"),
        (39, "しょんぼり"),
        (0, "しょんぼり"),
    ],
)
def test_mood(value: int, label: str) -> None:
    assert mood(value, value) == value
    assert mood_label(value) == label


def test_reverse_time_rejected() -> None:
    with pytest.raises(ValueError):
        decay(Stats(HATCH), START, START)
