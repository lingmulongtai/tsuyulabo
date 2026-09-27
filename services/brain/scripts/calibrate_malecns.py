"""Reproduce the offline MaleCNS global-scale sweep without changing artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.malecns import manifest
from tsuyu_brain.connectome.stimuli import cue_stimulus
from tsuyu_brain.params import default_params


def calibrate() -> list[dict[str, object]]:
    """Sweep only one global scale per circuit; keep inputs fixed at 180 Hz.

    This exploratory sweep uses seed 19, separate from evaluation seeds 71/81.
    It does not optimize the decoder or edit individual edges/thresholds.
    """
    params = default_params()
    records = []
    for name in ("feeding", "escape", "olfaction_mb", "steering", "grooming"):
        original = load_circuit(name, "malecns-v1.0")
        original_scale = manifest()["circuits"][name]["scale"]
        stimuli = {
            "feeding": ({}, {"Gr64f": 1}, {"Gr64f": 1, "Gr66a": 1}),
            "escape": ({}, {"LPLC2": 1, "LC4": 1}),
            "olfaction_mb": ({}, cue_stimulus("banana", "malecns-v1.0")),
            "steering": ({}, {"photoreceptor_L": 1, "photoreceptor_R": 1}),
            "grooming": ({}, {"JO": 1}),
        }[name]
        scales = (1 / 128, 1 / 64, 1 / 32, 1 / 16, 1 / 8, 1 / 4)
        if name == "escape":
            scales = (1 / 4096, 1 / 2048, 1 / 1024, 1 / 512, 1 / 256, *scales)
        elif name == "olfaction_mb":
            scales = (*scales, 0.1875, 0.375, 0.5, 1.0)
        for scale in scales:
            circuit = original.with_weights(original.weights * (scale / original_scale))
            rates = []
            for stimulus in stimuli:
                result = simulate(circuit, stimulus, params, batch=8, seed=19)
                groups = (
                    (*circuit.output_groups, "KC")
                    if name == "olfaction_mb"
                    else circuit.output_groups
                )
                rates.append({group: float(result.rates[group].mean()) for group in groups})
            row = {"circuit": name, "scale": scale, "input_rate_hz": 180, "rates": rates}
            records.append(row)
            print(json.dumps(row), flush=True)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("eval-results/brain/calibration-malecns.json")
    )
    args = parser.parse_args()
    torch.set_num_threads(1)
    records = calibrate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
