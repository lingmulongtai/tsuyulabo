from __future__ import annotations

from datetime import UTC, datetime, timedelta
from random import Random

import pytest
from tsuyulabo_api.domain.team import GatherState, energy_factor, gather, material_weights

START = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.mark.parametrize(
    "energy,factor", [(100, 1), (60, 1), (59.99, 0.6), (20, 0.6), (19.99, 0.2), (0, 0.2)]
)
def test_energy_factor(energy: float, factor: float) -> None:
    assert energy_factor(energy) == factor


def test_integrated_energy_and_partitioned_reads() -> None:
    state = GatherState(START)
    once = gather(state, START + timedelta(hours=20), Random(1), {})
    # 8h*1.6 + 8h*.96 + 4h*.32 = 21.76 items.
    assert len(once.bag) == 21 and once.pending_exp == 21
    assert once.item_progress == pytest.approx(0.76)
    assert once.energy == 0 and once.shizuku == pytest.approx(44)
    rng = Random(1)
    split = state
    for hour in range(1, 21):
        split = gather(split, START + timedelta(hours=hour), rng, {})
    assert split.bag == once.bag
    assert split.item_progress == pytest.approx(once.item_progress)
    assert split.shizuku == pytest.approx(once.shizuku)
    assert state.bag == ()


def test_bag_cap_and_bonuses() -> None:
    state = GatherState(START, level=60)
    result = gather(state, START + timedelta(hours=100), Random(1), {})
    assert len(result.bag) == 30 and result.energy == 0
    assert result.item_progress == 0 and result.shizuku == pytest.approx(56)
    unchanged = gather(result, START + timedelta(hours=200), Random(1), {})
    assert unchanged.bag == result.bag and unchanged.shizuku == result.shizuku
    result = gather(state, START + timedelta(hours=100), Random(1), {}, ["bag_up", "drop_bonus"])
    assert len(result.bag) == 40
    assert result.shizuku == pytest.approx(40 / 7.5 * 14 * 1.2)
    boosted = gather(
        GatherState(START), START + timedelta(hours=1), Random(1), {}, ["gather_s", "gather_m"]
    )
    assert len(boosted.bag) + boosted.item_progress == pytest.approx(1.6 * 1.24)


def test_preferences_rare_drop_and_seed() -> None:
    weights = material_weights({"banana": 1, "apple_vinegar": 0.5, "yeast": -1, "blue_light": 1})
    assert weights == {"banana": 3, "apple": 2, "grape": 1, "yeast": 1, "agar": 1}
    rng = Random(45)
    jelly = 0
    for _ in range(1000):
        result = gather(GatherState(START, level=60), START + timedelta(hours=4), rng, {})
        jelly += result.bag.count("royal_jelly")
    assert 220 < jelly < 380
    assert gather(GatherState(START), START, rng, {}) == GatherState(START)
    with pytest.raises(ValueError):
        gather(GatherState(START), START - timedelta(seconds=1), rng, {})
