"""Synthetic topology inspired by named fly cell types, not measured synapses."""

from __future__ import annotations

import torch

from tsuyu_brain.circuit import Circuit

VERSION = "toy-v0"
CIRCUIT_NAMES = ("olfaction_mb", "feeding", "escape", "steering", "grooming")
CUES = ("banana", "apple_vinegar", "yeast", "grape", "blue_light")


def build_circuit(name: str) -> Circuit:
    definitions = {
        "olfaction_mb": (
            {
                "ORN": 8,
                "PN": 8,
                "KC": 200,
                "APL": 1,
                "MBON_ap": 1,
                "MBON_av": 1,
                "PAM": 1,
                "PPL1": 1,
                "visual": 8,
            },
            ("ORN", "visual", "PAM", "PPL1"),
            ("MBON_ap", "MBON_av"),
        ),
        "feeding": (
            {"Gr64f": 8, "Gr66a": 8, "feeding_interneuron": 4, "MN9": 2},
            ("Gr64f", "Gr66a"),
            ("MN9",),
        ),
        "escape": ({"LPLC2": 8, "LC4": 8, "DNp01": 2}, ("LPLC2", "LC4"), ("DNp01",)),
        "steering": (
            {
                "photoreceptor_L": 8,
                "photoreceptor_R": 8,
                "DNa02_L": 4,
                "DNa02_R": 4,
                "walking_DN": 4,
            },
            ("photoreceptor_L", "photoreceptor_R"),
            ("DNa02_L", "DNa02_R", "walking_DN"),
        ),
        "grooming": ({"JO": 8, "aDN": 4}, ("JO",), ("aDN",)),
    }
    if name not in definitions:
        raise ValueError(f"unknown circuit: {name}")
    sizes, inputs, outputs = definitions[name]
    groups: dict[str, slice] = {}
    n = 0
    for group, size in sizes.items():
        groups[group] = slice(n, n + size)
        n += size
    weights = torch.zeros(n, n)
    signs = torch.ones(n)
    projections: list[tuple[str, str]] = []
    generator = torch.Generator().manual_seed(2718)

    def project(source: str, target: str, strength: float) -> None:
        shape = (sizes[source], sizes[target])
        # Heterogeneous synaptic weights make within-projection controls meaningful.
        block = strength * (0.7 + 0.6 * torch.rand(shape, generator=generator))
        weights[groups[source], groups[target]] = block
        if strength < 0:
            signs[groups[source]] = -1
        projections.append((source, target))

    if name == "feeding":
        project("Gr64f", "feeding_interneuron", 2.0)
        project("feeding_interneuron", "MN9", 5.0)
        project("Gr66a", "MN9", -9.0)
    elif name == "escape":
        project("LPLC2", "DNp01", 1.6)
        project("LC4", "DNp01", 1.6)
    elif name == "steering":
        project("photoreceptor_L", "DNa02_L", 0.4)
        project("photoreceptor_R", "DNa02_R", 0.4)
        # Convergent sensory channels recruit a selective subset of the DN pool.
        # Spreading the same synaptic mass loses coincidence at that target.
        for source, target in (("photoreceptor_L", "DNa02_L"), ("photoreceptor_R", "DNa02_R")):
            weights[groups[source], groups[target].start + 1 : groups[target].stop] = 0
        project("photoreceptor_L", "walking_DN", 0.8)
        project("photoreceptor_R", "walking_DN", 0.8)
    elif name == "grooming":
        project("JO", "aDN", 0.4)
        weights[groups["JO"], groups["aDN"].start + 1 : groups["aDN"].stop] = 0
    else:
        project("ORN", "PN", 0)
        weights[groups["ORN"], groups["PN"]] = torch.eye(8) * 14
        project("PN", "KC", 0)
        # Every KC has exactly six PN partners. The last 40 also receive vision.
        for kc in range(200):
            partners = torch.randperm(8, generator=generator)[:6]
            weights[groups["PN"].start + partners, groups["KC"].start + kc] = 2 + 12 * torch.rand(
                6, generator=generator
            )
        project("visual", "KC", 0)
        weights[groups["visual"], groups["KC"].stop - 40 : groups["KC"].stop] = 2.5
        project("KC", "APL", 0.12)
        project("APL", "KC", -1.5)
        project("KC", "MBON_ap", 0)
        project("KC", "MBON_av", 0)
        weights[groups["KC"], groups["MBON_ap"]] = 0.8
        weights[groups["KC"], groups["MBON_av"]] = 0.8
        # DAN groups are modulators; learning.py applies their activity to KC synapses.
    return Circuit(name, groups, weights, signs, inputs, outputs, projections=tuple(projections))


def cue_stimulus(cue: str) -> dict[str, torch.Tensor | float]:
    if cue not in CUES:
        raise ValueError(f"unknown cue: {cue}")
    if cue == "blue_light":
        return {"visual": 1.0}
    rates = torch.zeros(8)
    rates[CUES.index(cue)] = 1.0
    return {"ORN": rates}
