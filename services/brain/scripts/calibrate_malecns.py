"""Reproduce the MaleCNS homeostasis sweep with held-out calibration seed 19."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import torch
from tsuyu_brain.circuit import Circuit, simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.malecns import manifest
from tsuyu_brain.connectome.malecns_normalization import normalize_mbon_inputs
from tsuyu_brain.connectome.malecns_visual import normalize_steering
from tsuyu_brain.connectome.stimuli import cue_stimulus
from tsuyu_brain.params import default_params


def unnormalized(name: str) -> Circuit:
    """Recover integer counts using manifest factors, then restore the global scale.

    The raw-source audit separately verifies these counts against Feather files.
    Rounding removes float32 normalization roundoff, not measured synapses.
    """
    circuit = load_circuit(name, "malecns-v1.0")
    info = manifest()["circuits"][name]
    weights = circuit.weights.clone()
    normalization = info.get("normalization", {})
    for projection, gains in normalization.get("projection_factors", {}).items():
        source, target = projection.split("->")
        weights[circuit.groups[source], circuit.groups[target]] /= torch.tensor(gains)
    for sign, gains in normalization.get("source_sign_factors", {}).items():
        mask = circuit.signs == int(sign)
        weights[mask] /= torch.tensor(gains)
    counts = weights / info["scale"]
    if not torch.allclose(counts, counts.round(), rtol=1e-6, atol=1e-4):
        raise ValueError("normalization factors do not recover integer synapse counts")
    return replace(circuit.with_weights(counts.round() * info["scale"]), tonic={})


def calibrate() -> dict[str, object]:
    params = default_params()
    mb = unnormalized("olfaction_mb")
    stimulus = cue_stimulus("banana", mb.version)
    reference = simulate(mb, stimulus, params, batch=8, seed=19)
    records = []
    for budget in (20, 40, 60, 80, 100, 120):
        circuit, normalization = normalize_mbon_inputs(mb, reference.neuron_rates.mean(0), budget)
        result = simulate(circuit, stimulus, params, batch=8, seed=19)
        ap, av = result.rates["MBON_ap"].mean(1), result.rates["MBON_av"].mean(1)
        row = {
            "circuit": mb.name,
            "kc_budget": budget,
            "apl_factor": normalization["projection_factors"]["APL->MBON_ap"][0],
            "baseline_pi": float(((ap - av) / (ap + av + 1e-8)).mean()),
            "rates": {
                g: float(result.rates[g].mean()) for g in ("KC", "APL", "MBON_ap", "MBON_av")
            },
        }
        records.append(row)
        print(json.dumps(row), flush=True)
    steering = unnormalized("steering")
    for budget in (2, 4, 8):
        circuit, _ = normalize_steering(steering, budget)
        for stimulus in (
            {},
            {"photoreceptor_L": 1},
            {"photoreceptor_R": 1},
            {"photoreceptor_L": 1, "photoreceptor_R": 1},
        ):
            result = simulate(circuit, stimulus, params, batch=8, seed=19)
            row = {
                "circuit": steering.name,
                "sign_budget": budget,
                "tonic": circuit.tonic,
                "stimulus": stimulus,
                "rates": {g: float(result.rates[g].mean()) for g in circuit.output_groups},
            }
            records.append(row)
            print(json.dumps(row), flush=True)
    return {
        "seed": 19,
        "trials": 8,
        "input_rate_hz": 180,
        "duration_ms": 300,
        "selection": {
            "kc_budget": "40 is the tested budget closest to neutral untrained PI",
            "apl_factor": "untrained banana mean KC Hz / mean APL Hz; shared by both pools",
            "sign_budget": "4 balances E/I while retaining unilateral responses; 2 is weak",
            "tonic": "fixed 1.15 background current, matching walking baseline; never fit per cell",
            "scales": "retain previous global scales; no threshold, plasticity, or trait tuning",
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("eval-results/brain/calibration-malecns.json")
    )
    args = parser.parse_args()
    torch.set_num_threads(1)
    records = calibrate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf8", newline="\n")


if __name__ == "__main__":
    main()
