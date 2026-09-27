"""Pure Python facade for the game API and Shiori's copy-only experiments.

Persist ``FlyState.to_bytes()`` and restore with ``FlyState.from_bytes(blob)``.
The versioned UTF-8 JSON codec includes BrainParams and 400 little-endian float16
KC weights (base64); it never contains executable objects or shared wiring.
Store ``state.params.to_dict()`` alongside the blob for queryable parameters.
Sex values passed to ``generate_individual`` are lower-case ``m`` / ``f``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import torch

from tsuyu_brain.activity import activity
from tsuyu_brain.behavior import LABELS, scenario_features
from tsuyu_brain.decoder import default_decoder
from tsuyu_brain.individuality import generate_individual
from tsuyu_brain.learning import (
    FlyState,
    apply_training,
    choice_indices,
    new_fly_state,
    preference_index,
)
from tsuyu_brain.maze import maze_policy
from tsuyu_brain.params import BrainParams, default_params

__all__ = [
    "BehaviorContext",
    "FlyState",
    "BrainParams",
    "default_params",
    "generate_individual",
    "new_fly_state",
    "apply_training",
    "preference_index",
    "predict_behavior",
    "run_odor_choice",
    "activity",
    "maze_policy",
]


@dataclass(frozen=True)
class BehaviorContext:
    scenario: str = "rest"
    cue: str = "banana"
    intensity: float = 1.0
    seed: int = 0


def predict_behavior(
    state: FlyState, context: BehaviorContext | Mapping[str, object] | str
) -> dict[str, float]:
    if state.version != "toy-v0":
        raise ValueError(f"no validated behavior decoder for connectome version: {state.version}")
    if isinstance(context, str):
        context = BehaviorContext(scenario=context)
    elif isinstance(context, Mapping):
        context = BehaviorContext(**context)
    features = scenario_features(
        state, context.scenario, cue=context.cue, intensity=context.intensity, seed=context.seed
    )
    probabilities = default_decoder().predict(features)[0].tolist()
    return dict(zip(LABELS, probabilities, strict=True))


def run_odor_choice(state: FlyState, cue: str, trials: int, seed: int) -> dict[str, int]:
    indices = choice_indices(state, cue, seed, trials)
    # Decode independent binary trials from the per-trial neural preference.
    generator = torch.Generator().manual_seed(seed + 1)
    toward = int((torch.rand(trials, generator=generator) < (indices + 1) / 2).sum())
    return {"toward": toward, "away": trials - toward}
