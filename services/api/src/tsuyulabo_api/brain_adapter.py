"""Lazy facade; JSON transport envelopes wrap the engine's compact byte codec.

Rows store decoded bytes and parameters; training history is audit data only.
Legacy replay snapshots are accepted for conversion on writes or explicit backfill.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import asdict, is_dataclass, replace
from importlib import import_module
from typing import Any

from fastapi import Request

from tsuyulabo_api.domain.constants import CUES
from tsuyulabo_api.errors import APIError


class BrainAdapter:
    @property
    def api(self) -> Any:
        try:
            return import_module("tsuyu_brain.api")
        except ModuleNotFoundError as exc:
            raise APIError("brain_unavailable", "脳エンジンを準備中です", 503) from exc

    def restore(self, snapshot: dict[str, Any]) -> Any:
        if snapshot.get("state"):
            return self.api.FlyState.from_bytes(base64.b64decode(snapshot["state"], validate=True))
        params = (
            self.api.default_params()
            if snapshot.get("default", True)
            else self.api.generate_individual(**snapshot["individual"])
        )
        state = self.api.new_fly_state(params)
        for event in snapshot.get("training", []):
            state, _ = self.api.apply_training(state, **event)
        return state

    def encode(self, state: Any, training: list[dict[str, Any]]) -> dict[str, Any]:
        params = state.params
        return {
            "state": base64.b64encode(state.to_bytes()).decode("ascii"),
            "params": asdict(params) if is_dataclass(params) else dict(params),
            "training": deepcopy(training),
        }

    def new(self) -> dict[str, Any]:
        return self.encode(self.api.new_fly_state(self.api.default_params()), [])

    def eclose(
        self, snapshot: dict[str, Any], traits: list[str], sex: str, seed: int
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        params = self.api.generate_individual(traits=traits, sex=sex.lower(), seed=seed)
        # Adult gains change without replaying or changing the learned weights.
        state = replace(self.restore(snapshot), params=params)
        updated = self.encode(state, snapshot.get("training", []))
        return updated, updated["params"]

    def train(
        self, snapshot: dict[str, Any], cue: str, valence: str, strength: float, seed: int
    ) -> tuple[dict[str, Any], float]:
        event = {"cue": cue, "valence": valence, "strength": strength, "seed": seed}
        state, association = self.api.apply_training(self.restore(snapshot), **event)
        return self.encode(state, [*snapshot.get("training", []), event]), float(association)

    def preferences(self, snapshot: dict[str, Any]) -> dict[str, float]:
        state = self.restore(snapshot)
        return {
            cue: float(self.api.preference_index(state, cue, seed=0, trials=20)) for cue in CUES
        }

    def behavior(self, snapshot: dict[str, Any], context: dict[str, Any]) -> dict[str, float]:
        inputs = {
            key: context[key] for key in ("scenario", "cue", "intensity", "seed") if key in context
        }
        return self.api.predict_behavior(self.restore(snapshot), inputs)

    def experiment(self, snapshot: dict[str, Any], cue: str, trials: int, seed: int) -> dict:
        return self.api.run_odor_choice(self.restore(snapshot), cue, trials, seed)


def get_brain(request: Request) -> BrainAdapter:
    return getattr(request.app.state, "brain_adapter", BrainAdapter())
