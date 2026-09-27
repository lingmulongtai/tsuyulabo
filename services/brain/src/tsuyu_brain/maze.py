"""Cached circuit probes and a cheap directional rate readout for maze actions."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import TypedDict

from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.learning import FlyState, preference_index


class Direction(TypedDict):
    cues: dict[str, float]
    light: float
    open: bool


class MazeObservation(TypedDict):
    current: Direction
    forward: Direction
    left: Direction
    right: Direction


@lru_cache(maxsize=128)
def _preference(blob: bytes, cue: str) -> float:
    return preference_index(FlyState.from_bytes(blob), cue, seed=0, trials=20)


@lru_cache(maxsize=32)
def _steering(blob: bytes) -> tuple[float, float, float]:
    state = FlyState.from_bytes(blob)
    result = simulate(
        load_circuit("steering", state.version),
        {"photoreceptor_L": 0.5, "photoreceptor_R": 0.5},
        state.params,
        duration_ms=100,
        seed=0,
    )
    return tuple(
        float(result.rates[name].mean()) / 100 for name in ("walking_DN", "DNa02_L", "DNa02_R")
    )


def maze_policy(state: FlyState, observation: MazeObservation) -> dict[str, float]:
    """Return normalized action probabilities without mutating the adult's state.

    Neural probes are keyed by the serialized state, so changed weights cannot
    accidentally reuse an earlier learned preference. No per-step LIF run occurs.
    """
    blob = state.to_bytes()
    walk, left, right = _steering(blob)
    params = state.params
    current = observation["current"]
    logits = {
        "forward": 1.2 + walk + math.log(params.walking_gain),
        "left": left - 3 * params.turn_asymmetry,
        "right": right + 3 * params.turn_asymmetry,
        "stay": -1.5 - math.log(params.walking_gain),
    }
    for action in ("forward", "left", "right"):
        direction = observation[action]
        if not direction["open"]:
            logits[action] -= 2
            continue
        gradient = sum(
            _preference(blob, cue) * (value - current["cues"].get(cue, 0))
            for cue, value in direction["cues"].items()
        )
        logits[action] += 10 * params.orn_gain * gradient
        logits[action] += 3 * params.light_gain * (direction["light"] - current["light"])
    peak = max(logits.values())
    weights = {action: math.exp(value - peak) for action, value in logits.items()}
    if not observation["forward"]["open"]:
        weights["forward"] = 0
    total = sum(weights.values())
    return {action: value / total for action, value in weights.items()}
