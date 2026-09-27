"""Version-aware game cue encodings; fruit names are not fitted odor receptor maps."""

from __future__ import annotations

import torch

from tsuyu_brain.connectome import DEFAULT_VERSION, load_circuit
from tsuyu_brain.connectome.toy_v0 import CUES
from tsuyu_brain.connectome.toy_v0 import cue_stimulus as toy_stimulus

# Deliberate game convention. All bodies in a glomerulus receive the same rate.
CUE_GLOMERULI = {"banana": "DM1", "apple_vinegar": "DM2", "yeast": "DM3", "grape": "DM4"}


def cue_stimulus(cue: str, version: str = DEFAULT_VERSION) -> dict[str, torch.Tensor | float]:
    if cue not in CUES:
        raise ValueError(f"unknown cue: {cue}")
    if version == "toy-v0":
        return toy_stimulus(cue)
    circuit = load_circuit("olfaction_mb", version)
    if cue == "blue_light":
        return {"visual": 1.0}
    from tsuyu_brain.connectome.malecns import neuron_metadata

    rows = neuron_metadata("olfaction_mb")[circuit.groups["ORN"]]
    return {
        "ORN": torch.tensor([float(row["type"] == f"ORN_{CUE_GLOMERULI[cue]}") for row in rows])
    }
