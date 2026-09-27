"""Small cached neural readout for friendly territorial bouts."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import TypedDict

from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.learning import FlyState
from tsuyu_brain.maze import _steering


class SumoObservation(TypedDict):
    distance: float
    food_distance: float
    threat: float
    stamina: float


@lru_cache(maxsize=32)
def _escape(blob: bytes) -> float:
    state = FlyState.from_bytes(blob)
    result = simulate(
        load_circuit("escape", state.version),
        {"LPLC2": 0.6, "LC4": 0.6},
        state.params,
        duration_ms=100,
        seed=0,
    )
    return float(result.rates["DNp01"].mean()) / 100


@lru_cache(maxsize=32)
def _feeding(blob: bytes) -> float:
    state = FlyState.from_bytes(blob)
    result = simulate(
        load_circuit("feeding", state.version),
        {"Gr64f": 0.7},
        state.params,
        duration_ms=100,
        seed=0,
    )
    return float(result.rates["MN9"].mean()) / 100


def sumo_policy(state: FlyState, observation: SumoObservation) -> dict[str, float]:
    """Read escape, steering and feeding gain without altering the fly state."""
    blob = state.to_bytes()
    walk, _, _ = _steering(blob)
    params = state.params
    threat = max(0.0, min(1.0, observation["threat"]))
    stamina = max(0.0, min(1.1, observation["stamina"]))
    near = observation["distance"] <= 1.6
    food = max(0.0, 1 - observation["food_distance"] / 4)
    logits = {
        "approach": 1.0 + walk + params.walking_gain + _feeding(blob) * food,
        "lunge": (1.6 + stamina if near else -4.0),
        "wing_threat": (0.8 if near else -1.0) + stamina / 2,
        "hold": 0.2 + (1 - stamina),
        "retreat": -1.5
        + 1.5 * threat
        + _escape(blob)
        + params.escape_gain
        - 4 * (params.escape_threshold - 1),
    }
    peak = max(logits.values())
    weights = {action: math.exp(value - peak) for action, value in logits.items()}
    total = sum(weights.values())
    return {action: value / total for action, value in weights.items()}
