from __future__ import annotations

import time
from dataclasses import replace

import pytest
from tsuyu_brain.api import apply_training, default_params, maze_policy, new_fly_state


def observation() -> dict:
    return {
        "current": {"cues": {"banana": 0.3}, "light": 0.1, "open": True},
        "forward": {"cues": {"banana": 1.0}, "light": 0.1, "open": True},
        "left": {"cues": {"banana": 0.1}, "light": 0.1, "open": True},
        "right": {"cues": {"banana": 0.1}, "light": 0.1, "open": True},
    }


def test_training_increases_movement_toward_banana() -> None:
    state = new_fly_state(default_params())
    trained = state
    for seed in range(3):
        trained, _ = apply_training(trained, "banana", "reward", 1, seed)
    assert (
        maze_policy(trained, observation())["forward"]
        > maze_policy(state, observation())["forward"]
    )


def test_turn_bias_walls_determinism_and_speed() -> None:
    state = new_fly_state(default_params())
    right = replace(state, params=replace(state.params, turn_asymmetry=0.15))
    inputs = observation()
    assert maze_policy(right, inputs)["right"] > maze_policy(state, inputs)["right"]
    inputs["forward"]["open"] = False
    expected = maze_policy(state, inputs)
    assert expected["forward"] == 0
    assert sum(expected.values()) == pytest.approx(1)
    started = time.perf_counter()
    for _ in range(400):
        assert maze_policy(state, inputs) == expected
    assert time.perf_counter() - started < 1
