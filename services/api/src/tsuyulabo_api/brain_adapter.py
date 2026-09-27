"""Lazy façade boundary; no engine internals or pickle in persisted state.

Until the engine defines its byte codec, snapshots contain individual generation
inputs and the short, seeded training history (at most 18 entries per week).
Reconstruction uses only public façade calls and preserves learning at eclosion.
The commander can replace this codec without changing routers or stored effects.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, is_dataclass
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

    def params(self, snapshot: dict[str, Any]) -> Any:
        api = self.api
        if snapshot["default"]:
            # W1's default_params is expected to be re-exported by the public façade.
            return api.default_params()
        return api.generate_individual(**snapshot["individual"])

    def restore(self, snapshot: dict[str, Any]) -> Any:
        state = self.api.new_fly_state(self.params(snapshot))
        for event in snapshot["training"]:
            state, _ = self.api.apply_training(state, **event)
        return state

    def new(self) -> dict[str, Any]:
        snapshot = {"default": True, "individual": {}, "training": []}
        self.restore(snapshot)
        return snapshot

    def eclose(
        self, snapshot: dict[str, Any], traits: list[str], sex: str, seed: int
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        snapshot = deepcopy(snapshot)
        snapshot.update(default=False, individual={"traits": traits, "sex": sex, "seed": seed})
        self.restore(snapshot)
        params = self.params(snapshot)
        encoded = asdict(params) if is_dataclass(params) else dict(params)
        return snapshot, encoded

    def train(
        self, snapshot: dict[str, Any], cue: str, valence: str, strength: float, seed: int
    ) -> tuple[dict[str, Any], float]:
        event = {"cue": cue, "valence": valence, "strength": strength, "seed": seed}
        _, association = self.api.apply_training(self.restore(snapshot), **event)
        updated = deepcopy(snapshot)
        updated["training"].append(event)
        return updated, float(association)

    def preferences(self, snapshot: dict[str, Any]) -> dict[str, float]:
        state = self.restore(snapshot)
        return {
            cue: float(self.api.preference_index(state, cue, seed=0, trials=100)) for cue in CUES
        }

    def behavior(self, snapshot: dict[str, Any], context: dict[str, Any]) -> dict[str, float]:
        return self.api.predict_behavior(self.restore(snapshot), context)

    def experiment(self, snapshot: dict[str, Any], cue: str, trials: int, seed: int) -> dict:
        return self.api.run_odor_choice(deepcopy(self.restore(snapshot)), cue, trials, seed)


def get_brain(request: Request) -> BrainAdapter:
    return getattr(request.app.state, "brain_adapter", BrainAdapter())
