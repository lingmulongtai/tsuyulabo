"""Dopamine-gated KC plasticity and compact per-fly state."""

from __future__ import annotations

import base64
import json
import math
from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

from tsuyu_brain.circuit import Circuit, simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.toy_v0 import cue_stimulus
from tsuyu_brain.params import BrainParams


@dataclass(frozen=True)
class FlyState:
    params: BrainParams
    kc_mbon: Tensor  # [200, 2], columns approach / avoid; owned by this state
    version: str = "toy-v0"

    def __post_init__(self) -> None:
        if self.version != "toy-v0" or self.kc_mbon.shape != (200, 2):
            raise ValueError("unsupported state version or weight shape")
        if not torch.isfinite(self.kc_mbon).all() or (self.kc_mbon < 0).any():
            raise ValueError("learned weights must be finite and nonnegative")
        if (self.kc_mbon > 65504).any():
            raise ValueError("weights exceed float16 storage range")

    def to_bytes(self) -> bytes:
        weights = self.kc_mbon.detach().cpu().numpy().astype("<f2").tobytes()
        return json.dumps(
            {
                "version": self.version,
                "params": self.params.to_dict(),
                "kc_mbon_f16": base64.b64encode(weights).decode("ascii"),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, payload: bytes) -> FlyState:
        data = json.loads(payload)
        raw = base64.b64decode(data["kc_mbon_f16"], validate=True)
        if len(raw) != 800:
            raise ValueError("expected 400 float16 weights")
        weights = torch.from_numpy(np.frombuffer(raw, dtype="<f2").astype("float32")).reshape(
            200, 2
        )
        return cls(BrainParams(**data["params"]), weights, data["version"])


def new_fly_state(params: BrainParams) -> FlyState:
    circuit = load_circuit("olfaction_mb")
    weights = torch.cat(
        [
            circuit.weights[circuit.groups["KC"], circuit.groups[group]]
            for group in ("MBON_ap", "MBON_av")
        ],
        dim=1,
    )
    return FlyState(params, weights.clone())


def learned_circuit(state: FlyState) -> Circuit:
    circuit = load_circuit("olfaction_mb", state.version)
    weights = circuit.weights.clone()
    for column, name in enumerate(("MBON_ap", "MBON_av")):
        weights[circuit.groups["KC"], circuit.groups[name]] = state.kc_mbon[:, column : column + 1]
    return circuit.with_weights(weights)


def choice_indices(state: FlyState, cue: str, seed: int, trials: int) -> Tensor:
    if trials < 1:
        raise ValueError("trials must be positive")
    result = simulate(
        learned_circuit(state),
        cue_stimulus(cue),
        state.params,
        duration_ms=300,
        batch=trials,
        seed=seed,
    )
    ap = result.rates["MBON_ap"].mean(1)
    av = result.rates["MBON_av"].mean(1)
    return (ap - av) / (ap + av + 1e-8)


def preference_index(state: FlyState, cue: str, seed: int = 0, trials: int = 20) -> float:
    return float(choice_indices(state, cue, seed, trials).mean())


def apply_training(
    state: FlyState, cue: str, valence: str, strength: float, seed: int
) -> tuple[FlyState, float]:
    if valence not in {"reward", "punish"}:
        raise ValueError("valence must be reward or punish")
    if not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be in [0, 1]")
    stimulus = cue_stimulus(cue)
    dan = "PAM" if valence == "reward" else "PPL1"
    stimulus[dan] = 1.0
    circuit = learned_circuit(state)
    result = simulate(circuit, stimulus, state.params, batch=8, seed=seed)
    trace = (result.neuron_rates[:, circuit.groups["KC"]].mean(0) / 40).clamp(0, 1)
    dan_activity = (result.rates[dan].mean() / state.params.input_rate_hz).clamp(0, 1)
    weights = state.kc_mbon.clone()
    column = 1 if valence == "reward" else 0
    weights[:, column] = (
        weights[:, column] - state.params.learning_rate * strength * trace * dan_activity
    ).clamp_min(0)
    updated = FlyState(state.params, weights, state.version)
    return updated, preference_index(updated, cue, seed, trials=8)
