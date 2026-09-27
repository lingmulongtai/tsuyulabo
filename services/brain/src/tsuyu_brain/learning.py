"""Dopamine-gated KC plasticity and compact per-fly state."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

import torch
from torch import Tensor

from tsuyu_brain.circuit import Circuit, simulate
from tsuyu_brain.connectome import DEFAULT_VERSION, load_circuit
from tsuyu_brain.connectome.stimuli import cue_stimulus
from tsuyu_brain.params import BrainParams
from tsuyu_brain.state_codec import decode_weights, encode_weights


@dataclass(frozen=True)
class FlyState:
    params: BrainParams
    kc_mbon: Tensor  # magnitudes [KC, all approach MBONs then all avoid MBONs]
    version: str = DEFAULT_VERSION

    def __post_init__(self) -> None:
        if self.kc_mbon.shape != learning_shape(self.version):
            raise ValueError("unsupported state version or weight shape")
        if not torch.isfinite(self.kc_mbon).all() or (self.kc_mbon < 0).any():
            raise ValueError("learned weights must be finite and nonnegative")
        if (self.kc_mbon > 65504).any():
            raise ValueError("weights exceed float16 storage range")

    def to_bytes(self) -> bytes:
        return json.dumps(
            {
                "version": self.version,
                "params": self.params.to_dict(),
                **encode_weights(self.kc_mbon, self.version),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, payload: bytes) -> FlyState:
        data = json.loads(payload)
        weights = decode_weights(data, learning_shape(data["version"]))
        return cls(BrainParams(**data["params"]), weights, data["version"])


def learning_shape(version: str) -> tuple[int, int]:
    circuit = load_circuit("olfaction_mb", version)
    sizes = {name: group.stop - group.start for name, group in circuit.groups.items()}
    return sizes["KC"], sizes["MBON_ap"] + sizes["MBON_av"]


def new_fly_state(params: BrainParams, version: str = DEFAULT_VERSION) -> FlyState:
    circuit = load_circuit("olfaction_mb", version)
    weights = torch.cat(
        [
            circuit.weights[circuit.groups["KC"], circuit.groups[group]]
            for group in ("MBON_ap", "MBON_av")
        ],
        dim=1,
    )
    return FlyState(params, weights.abs().clone(), version)


def learned_circuit(state: FlyState) -> Circuit:
    circuit = load_circuit("olfaction_mb", state.version)
    weights = circuit.weights.clone()
    column = 0
    for name in ("MBON_ap", "MBON_av"):
        group = circuit.groups[name]
        stop = column + group.stop - group.start
        weights[circuit.groups["KC"], group] = (
            state.kc_mbon[:, column:stop] * circuit.signs[circuit.groups["KC"], None]
        )
        column = stop
    return circuit.with_weights(weights)


def choice_indices(state: FlyState, cue: str, seed: int, trials: int) -> Tensor:
    if trials < 1:
        raise ValueError("trials must be positive")
    result = simulate(
        learned_circuit(state),
        cue_stimulus(cue, state.version),
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
    stimulus = cue_stimulus(cue, state.version)
    dan = "PAM" if valence == "reward" else "PPL1"
    stimulus[dan] = 1.0
    circuit = learned_circuit(state)
    result = simulate(circuit, stimulus, state.params, batch=8, seed=seed)
    trace = (result.neuron_rates[:, circuit.groups["KC"]].mean(0) / 40).clamp(0, 1)
    dan_activity = (result.rates[dan].mean() / state.params.input_rate_hz).clamp(0, 1)
    weights = state.kc_mbon.clone()
    approach = circuit.groups["MBON_ap"]
    split = approach.stop - approach.start
    columns = slice(split, None) if valence == "reward" else slice(0, split)
    weights[:, columns] = (
        weights[:, columns] - state.params.learning_rate * strength * trace[:, None] * dan_activity
    ).clamp_min(0)
    updated = FlyState(state.params, weights, state.version)
    return updated, preference_index(updated, cue, seed, trials=8)
