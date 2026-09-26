from __future__ import annotations

import pytest
from tsuyu_brain.api import (
    apply_training,
    generate_individual,
    new_fly_state,
    predict_behavior,
    run_odor_choice,
)
from tsuyu_brain.behavior import LABELS


def test_copy_only_odor_experiment() -> None:
    state = new_fly_state(generate_individual([], "f", 1))
    for seed in range(3):
        state, _ = apply_training(state, "banana", "reward", 1, seed)
    before = state.to_bytes()
    result = run_odor_choice(state, "banana", trials=20, seed=4)
    assert result == run_odor_choice(state, "banana", trials=20, seed=4)
    assert sum(result.values()) == 20
    assert result["toward"] > result["away"]
    assert state.to_bytes() == before


def test_behavior_probabilities() -> None:
    state = new_fly_state(generate_individual([], "m", 1))
    result = predict_behavior(state, {"scenario": "sugar", "seed": 2})
    assert set(result) == set(LABELS)
    assert sum(result.values()) == pytest.approx(1)
    assert min(result.values()) >= 0
    assert max(result, key=result.get) == "feed"
