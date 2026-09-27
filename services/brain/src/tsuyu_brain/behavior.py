"""Scenario stimuli mapped to output-neuron firing-rate features."""

from __future__ import annotations

from dataclasses import replace

import torch
from torch import Tensor

from tsuyu_brain.circuit import Circuit, simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.stimuli import cue_stimulus
from tsuyu_brain.learning import FlyState, learned_circuit

FEATURES = ("MN9", "DNp01", "DNa02_L", "DNa02_R", "walking_DN", "aDN", "MBON_ap", "MBON_av")
LABELS = ("rest", "walk", "turn_left", "turn_right", "feed", "escape", "groom", "approach", "avoid")
SCENARIOS = {
    "rest": "rest",
    "walk": "walk",
    "sugar": "feed",
    "bitter": "rest",
    "sugar+bitter": "rest",
    "looming": "escape",
    "light_left": "turn_left",
    "light_right": "turn_right",
    "antenna_touch": "groom",
    "liked_odor": "approach",
    "disliked_odor": "avoid",
}


def shuffled_wiring(circuit: Circuit, seed: int) -> Circuit:
    """Permute all entries (including zeros) independently within each projection.

    Cell groups, signs, and each projection's weight distribution stay fixed.
    Learned KC weights are permuted too; the frozen decoder is never retrained.
    """
    generator = torch.Generator().manual_seed(seed)
    weights = circuit.weights.clone()
    for source, target in circuit.projections:
        block = weights[circuit.groups[source], circuit.groups[target]]
        # Real functional groups may contain both signs; shuffle within sign strata.
        signs = circuit.signs[circuit.groups[source]]
        for sign in signs.unique():
            rows = signs == sign
            flat = block[rows].flatten()
            block[rows] = flat[torch.randperm(flat.numel(), generator=generator)].reshape(
                int(rows.sum()), block.shape[1]
            )
    return circuit.with_weights(weights)


def scenario_features(
    state: FlyState,
    scenario: str,
    *,
    cue: str = "banana",
    intensity: float = 1.0,
    batch: int = 1,
    seed: int = 0,
    duration_ms: float = 300,
    shuffle_seed: int | None = None,
) -> Tensor:
    """Return [batch, 8] time-averaged rates. Odor states must already be trained.

    Walk adds a tonic arousal drive; rest retains low spontaneous walking-DN firing.
    Scenario names never enter the decoder's numeric input.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")
    if not 0 <= intensity <= 5:
        raise ValueError("intensity must be in [0, 5]")
    params = state.params
    if scenario == "walk":
        params = replace(params, walking_current=params.walking_current + 1.5 * intensity)
    jobs: dict[str, dict[str, float | Tensor]] = {"steering": {}}
    if scenario in {"sugar", "bitter", "sugar+bitter"}:
        jobs["feeding"] = {}
        if "sugar" in scenario:
            jobs["feeding"]["Gr64f"] = intensity
        if "bitter" in scenario:
            jobs["feeding"]["Gr66a"] = intensity
    elif scenario == "looming":
        jobs["escape"] = {"LPLC2": intensity, "LC4": intensity}
    elif scenario in {"light_left", "light_right"}:
        jobs["steering"] = {
            "photoreceptor_L" if scenario == "light_left" else "photoreceptor_R": intensity
        }
    elif scenario == "antenna_touch":
        jobs["grooming"] = {"JO": intensity}
    elif scenario in {"liked_odor", "disliked_odor"}:
        jobs["olfaction_mb"] = {
            name: value * intensity for name, value in cue_stimulus(cue, state.version).items()
        }
    features = torch.zeros(batch, len(FEATURES))
    for name, stimulus in jobs.items():
        circuit = (
            learned_circuit(state) if name == "olfaction_mb" else load_circuit(name, state.version)
        )
        if shuffle_seed is not None:
            circuit = shuffled_wiring(circuit, shuffle_seed)
        result = simulate(circuit, stimulus, params, duration_ms, batch, seed)
        for group in circuit.output_groups:
            features[:, FEATURES.index(group)] = (result.rates[group] * result.window_ms).sum(
                1
            ) / duration_ms
    return features
