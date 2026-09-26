from __future__ import annotations

from random import Random

import pytest
from tsuyulabo_api.domain.adults import (
    AdultProgress,
    add_exp,
    bonuses,
    exp_threshold,
    level_cap,
    level_up,
    level_up_cost,
    unlock_subskills,
)


@pytest.mark.parametrize("stars,cap", [(1, 20), (2, 30), (3, 40), (4, 50), (5, 60)])
def test_caps_and_unlocks(stars: int, cap: int) -> None:
    assert level_cap(stars) == cap
    state = add_exp(AdultProgress(stars), 100000, Random(1))
    assert state.level == cap and state.exp == 0
    assert set(dict(state.subskills)) == {n for n in (10, 25, 50) if n <= cap}
    with pytest.raises(ValueError, match="cap"):
        level_up(state, 100000, Random(1))


def test_thresholds_paid_level_and_fixed_rolls() -> None:
    assert level_up_cost(9) == 180 and exp_threshold(9) == 90
    state = add_exp(AdultProgress(5), 29, Random(1))
    assert (state.level, state.exp) == (2, 19)
    state = add_exp(state, 1, Random(1))
    assert (state.level, state.exp) == (3, 0)
    state, cost = level_up(AdultProgress(5, 9, 7), 180, Random(1))
    assert (state.level, state.exp, cost) == (10, 7, 180)
    rng = Random(99)
    before = rng.getstate()
    assert unlock_subskills(rng, 10, dict(state.subskills)) == dict(state.subskills)
    assert rng.getstate() == before
    with pytest.raises(ValueError, match="insufficient"):
        level_up(state, 0, rng)
    result = bonuses(["gather_s", "gather_m", *(["great_up"] * 8), "bag_up", "rp_up"])
    assert result["gather_bonus"] == 0.24
    assert result["great_bonus"] == 0.10 and result["bag_bonus"] == 10
