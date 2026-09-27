"""The only module that knows the evolving W1 brain serialization contract."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Protocol


@dataclass(frozen=True)
class BrainSnapshot:
    fly_id: str
    params: dict[str, Any] = field(default_factory=dict)
    learned_weights: bytes | None = None
    training: list[dict[str, Any]] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    sex: str = "F"


class BrainEngine(Protocol):
    def run_odor_choice(
        self, snapshot: BrainSnapshot, cue: str, trials: int, seed: int
    ) -> dict[str, int]: ...


class BrainUnavailable(RuntimeError):
    pass


class RealBrainEngine:
    """Lazy façade import; never replace real results with fake measurements.

    Adult blobs use FlyState.from_bytes; without a blob reconstruct from persisted
    params and replay training. This seam is intentionally isolated for the W1 merge.
    """

    def run_odor_choice(
        self, snapshot: BrainSnapshot, cue: str, trials: int, seed: int
    ) -> dict[str, int]:
        try:
            api = import_module("tsuyu_brain.api")
        except ModuleNotFoundError as exc:
            raise BrainUnavailable("tsuyu_brain.api is not installed") from exc
        copied = deepcopy(snapshot)
        if copied.learned_weights is not None:
            try:
                learning = import_module("tsuyu_brain.learning")
                state = learning.FlyState.from_bytes(copied.learned_weights)
            except (AttributeError, ModuleNotFoundError) as exc:
                raise BrainUnavailable(
                    "wire the W1 FlyState byte decoder in brain_adapter.py"
                ) from exc
        else:
            if copied.params:
                params_module = import_module("tsuyu_brain.params")
                params = params_module.BrainParams(**copied.params)
            else:
                individual_seed = int.from_bytes(
                    hashlib.sha256(copied.fly_id.encode()).digest()[:4]
                )
                params = api.generate_individual(copied.traits, copied.sex, individual_seed)
            state = api.new_fly_state(params)
            for index, training in enumerate(copied.training):
                state, _ = api.apply_training(
                    state,
                    training["cue"],
                    training["valence"],
                    training.get("learning_strength", training.get("strength", 0.0)),
                    training.get("seed", index),
                )
        result = api.run_odor_choice(deepcopy(state), cue, trials, seed)
        return {"toward": int(result["toward"]), "away": int(result["away"])}


class FakeBrainEngine:
    """Explicit test double with deterministic counts and no brain imports."""

    def run_odor_choice(
        self, snapshot: BrainSnapshot, cue: str, trials: int, seed: int
    ) -> dict[str, int]:
        copied = deepcopy(snapshot)
        value = copied.params.get("associations", {}).get(cue, 0.0)
        for training in copied.training:
            if training.get("cue") == cue:
                value += training.get("learning_strength", training.get("strength", 0.1)) * (
                    1 if training["valence"] == "reward" else -1
                )
        toward = round(trials * (max(-1.0, min(1.0, value)) + 1) / 2)
        return {"toward": toward, "away": trials - toward}
