"""Inspect output responsiveness and grouped development accuracy; never score test rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from calibrate_malecns import unnormalized
from tsuyu_brain import learning
from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.malecns import manifest
from tsuyu_brain.connectome.malecns_normalization import normalize_mbon_inputs
from tsuyu_brain.connectome.stimuli import cue_stimulus
from tsuyu_brain.decoder.dataset import generate_dataset, split_dataset
from tsuyu_brain.decoder.diagnostics import feature_diagnostics
from tsuyu_brain.decoder.model import evaluate_decoder, train_decoder
from tsuyu_brain.learning import apply_training, learned_circuit, new_fly_state
from tsuyu_brain.params import default_params


def probe() -> dict[str, object]:
    params = default_params()
    feeding = load_circuit("feeding", "malecns-v1.0")
    feeding_rows = []
    # Only the documented circuit-wide weight scale is varied; no cell-specific fitting.
    for factor in (0.75, 1.0, 1.25, 1.5, 2.0):
        circuit = feeding.with_weights(feeding.weights * factor)
        row = {"scale": manifest()["circuits"]["feeding"]["scale"] * factor}
        for name, stimulus in (("sugar", {"Gr64f": 1}), ("mixed", {"Gr64f": 1, "Gr66a": 1})):
            result = simulate(circuit, stimulus, params, batch=32, seed=19)
            row[name] = {
                group: {
                    "hz": float(result.rates[group].mean()),
                    "silent_trials": int((result.rates[group].sum(1) == 0).sum()),
                }
                for group in circuit.output_groups
            }
        feeding_rows.append(row)
    odors = []
    for cue in ("banana", "apple_vinegar", "yeast", "grape"):
        for valence in ("reward", "punish"):
            state = new_fly_state(params, "malecns-v1.0")
            for repetition in range(3):
                state, _ = apply_training(state, cue, valence, 1, 19 + repetition)
            circuit = learned_circuit(state)
            result = simulate(circuit, cue_stimulus(cue, state.version), params, batch=8, seed=19)
            odors.append(
                {
                    "cue": cue,
                    "training": valence,
                    "upstream_rates": {
                        group: float(result.rates[group].mean())
                        for group in ("ORN", "PN", "KC", "APL")
                    },
                    "active_kcs": int(
                        (result.neuron_rates[:, circuit.groups["KC"]].sum(0) > 0).sum()
                    ),
                    "rates": {
                        group: float(result.rates[group].mean()) for group in circuit.output_groups
                    },
                }
            )
    return {"seed": 19, "feeding_global_scale_sweep": feeding_rows, "odor_outputs": odors}


def mb_scale_sweep() -> list[dict[str, object]]:
    """Reapply the existing normalization formula after a circuit-wide scale change."""
    params = default_params()
    base = unnormalized("olfaction_mb")
    original_loader = learning.load_circuit
    records = []
    try:
        for scale in (0.09375, 0.140625, 0.1875, 0.234375, 0.28125, 0.375):
            factor = scale / manifest()["circuits"]["olfaction_mb"]["scale"]
            raw = base.with_weights(base.weights * factor)
            stimulus = cue_stimulus("banana", base.version)
            reference = simulate(raw, stimulus, params, batch=8, seed=19)
            circuit, _ = normalize_mbon_inputs(raw, reference.neuron_rates.mean(0))
            learning.load_circuit = lambda name, version, candidate=circuit: (
                candidate if name == "olfaction_mb" else original_loader(name, version)
            )
            row = {"scale": scale, "cues": {}}
            for cue in ("banana", "apple_vinegar", "yeast", "grape"):
                original = new_fly_state(params, "malecns-v1.0")
                before = learning.preference_index(original, cue, 19, 8)
                results = {"baseline_pi": before}
                for valence in ("reward", "punish"):
                    state = original
                    for repetition in range(3):
                        state, _ = apply_training(state, cue, valence, 1, 19 + repetition)
                    result = simulate(
                        learned_circuit(state),
                        cue_stimulus(cue, state.version),
                        params,
                        batch=8,
                        seed=19,
                    )
                    ap, av = result.rates["MBON_ap"].mean(1), result.rates["MBON_av"].mean(1)
                    results[valence] = {
                        "delta_pi": float(((ap - av) / (ap + av + 1e-8)).mean()) - before,
                        "rates": {g: float(result.rates[g].mean()) for g in circuit.output_groups},
                    }
                row["cues"][cue] = results
            records.append(row)
            print(json.dumps(row), flush=True)
    finally:
        learning.load_circuit = original_loader
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--development", action="store_true")
    parser.add_argument("--mb-scale-sweep", action="store_true")
    parser.add_argument("--mb-scale", type=float)
    args = parser.parse_args()
    torch.set_num_threads(1)
    if args.mb_scale is not None:
        base = unnormalized("olfaction_mb")
        scale = manifest()["circuits"]["olfaction_mb"]["scale"]
        raw = base.with_weights(base.weights * (args.mb_scale / scale))
        reference = simulate(
            raw, cue_stimulus("banana", base.version), default_params(), batch=8, seed=19
        )
        candidate, _ = normalize_mbon_inputs(raw, reference.neuron_rates.mean(0))
        original_loader = learning.load_circuit
        learning.load_circuit = lambda name, version: (
            candidate if name == "olfaction_mb" else original_loader(name, version)
        )
        report = {"mb_global_scale": args.mb_scale, "calibration_seed": 19}
    else:
        report = {"mb_global_scale_sweep": mb_scale_sweep()} if args.mb_scale_sweep else probe()
    report["bundle_scales"] = {name: row["scale"] for name, row in manifest()["circuits"].items()}
    print(json.dumps(report), flush=True)
    if args.development:
        train, _ = split_dataset(generate_dataset(version="malecns-v1.0"))
        fit, validation = split_dataset(train)
        report["development"] = {
            "fit_individuals": fit.individuals.unique().tolist(),
            "validation_individuals": validation.individuals.unique().tolist(),
            "diagnostics": feature_diagnostics(validation),
            **{
                kind: evaluate_decoder(train_decoder(fit, kind), validation)
                for kind in ("logistic", "mlp")
            },
        }
        print(json.dumps(report["development"]), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n")


if __name__ == "__main__":
    main()
