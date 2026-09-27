from __future__ import annotations

import pytest
import torch
from tsuyu_brain.behavior import scenario_features
from tsuyu_brain.individuality import generate_individual
from tsuyu_brain.learning import new_fly_state


@pytest.mark.parametrize("shuffle_seed", [None, 41])
@pytest.mark.parametrize("trait", ["right_turner", "wanderer", "easygoing"])
def test_measured_features_remove_individual_rest_without_removing_walk(
    trait: str, shuffle_seed: int | None
) -> None:
    state = new_fly_state(generate_individual([trait], "f", 123), "malecns-v1.0")
    before = state.to_bytes()
    rest = scenario_features(state, "rest", batch=2, shuffle_seed=shuffle_seed)
    walk = scenario_features(state, "walk", batch=2, shuffle_seed=shuffle_seed)
    assert rest.shape == walk.shape == (2, 68)
    assert torch.equal(rest, torch.zeros_like(rest))
    assert (walk[:, 4] > 0).all()
    assert state.to_bytes() == before
