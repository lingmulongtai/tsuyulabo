"""Reproducible evaluation table: uv run python -m tsuyu_brain.eval."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from scipy.stats import ttest_ind

from tsuyu_brain.behavior import LABELS
from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.decoder.dataset import generate_dataset, split_dataset
from tsuyu_brain.decoder.model import evaluate_decoder, train_decoder
from tsuyu_brain.individuality import generate_individual
from tsuyu_brain.learning import apply_training, new_fly_state, preference_index
from tsuyu_brain.params import default_params


def sanity_metrics() -> dict[str, dict[str, object]]:
    params = default_params()
    feeding, escape = load_circuit("feeding"), load_circuit("escape")

    def feed(stimulus: dict[str, float]) -> float:
        return float(simulate(feeding, stimulus, params, batch=16, seed=81).rates["MN9"].mean())

    rest, sugar, mixed = feed({}), feed({"Gr64f": 1}), feed({"Gr64f": 1, "Gr66a": 1})
    shadow = float(
        simulate(escape, {"LPLC2": 1, "LC4": 1}, params, batch=16, seed=81).rates["DNp01"].mean()
    )
    quiet = float(simulate(escape, {}, params, batch=16, seed=81).rates["DNp01"].mean())
    original = new_fly_state(params)
    baseline = preference_index(original, "banana", 71, 32)
    learned = {}
    for valence in ("reward", "punish"):
        state = original
        for repetition in range(3):
            state, _ = apply_training(state, "banana", valence, 1, repetition)
        learned[valence] = preference_index(state, "banana", 71, 32) - baseline
    return {
        "sugar_mn9": {
            "passed": sugar > 0 and sugar >= 5 * rest,
            "rest_hz": rest,
            "sugar_hz": sugar,
        },
        "looming_dnp01": {
            "passed": shadow > 0 and quiet == 0,
            "rest_hz": quiet,
            "looming_hz": shadow,
        },
        "bitter_suppression": {"passed": mixed < 0.5 * sugar, "sugar_hz": sugar, "mixed_hz": mixed},
        "learning": {
            "passed": learned["reward"] >= 0.3 and learned["punish"] <= -0.3,
            "baseline_pi": baseline,
            "reward_delta": learned["reward"],
            "punish_delta": learned["punish"],
        },
    }


def trait_metrics(population: int = 32) -> dict[str, object]:
    """Independent populations under equal bilateral illumination; one-sided Welch test."""
    rates: list[list[float]] = [[], []]
    for group, traits in enumerate(([], ["right_turner"])):
        for individual in range(population):
            seed = 15000 + group * 10000 + individual
            params = generate_individual(traits, "m" if individual % 2 else "f", seed)
            result = simulate(
                load_circuit("steering"),
                {"photoreceptor_L": 1, "photoreceptor_R": 1},
                params,
                batch=4,
                seed=seed,
            )
            right = result.rates["DNa02_R"].mean()
            left = result.rates["DNa02_L"].mean()
            rates[group].append(float(right / (right + left + 1e-8)))
    p = float(ttest_ind(rates[1], rates[0], equal_var=False, alternative="greater").pvalue)
    means = [sum(group) / population for group in rates]
    return {
        "passed": means[1] > means[0] and p < 0.01,
        "wild_mean_right_fraction": means[0],
        "trait_mean_right_fraction": means[1],
        "p_one_sided": p,
        "individuals_per_group": population,
    }


def decoder_metrics() -> dict[str, object]:
    data = generate_dataset()
    train, held_out = split_dataset(data)
    metrics: dict[str, object] = {
        "labels": LABELS,
        "train_rows": len(train.labels),
        "test_rows": len(held_out.labels),
    }
    models = {}
    for kind in ("logistic", "mlp"):
        models[kind] = train_decoder(train, kind)
        metrics[kind] = evaluate_decoder(models[kind], held_out)
    control_accuracies = []
    for seed in (41, 42, 43):
        _, control = split_dataset(generate_dataset(shuffle_seed=seed))
        result = evaluate_decoder(models["mlp"], control)
        metrics[f"shuffled_{seed}"] = result
        control_accuracies.append(result["accuracy"])
    accuracy = metrics["mlp"]["accuracy"]
    drop = accuracy - sum(control_accuracies) / len(control_accuracies)
    metrics.update(
        {
            "accuracy_drop": drop,
            "minimum_drop": 0.10,
            "passed": accuracy >= 0.85 and metrics["logistic"]["accuracy"] >= 0.85 and drop >= 0.10,
        }
    )
    return metrics


def run_evaluation() -> dict[str, object]:
    checks = sanity_metrics()
    checks["trait_bias"] = trait_metrics()
    checks["decoder"] = decoder_metrics()
    return {
        "connectome": "toy-v0",
        "model_boundary": "synthetic, not biological validation",
        "torch_version": str(torch.__version__),
        "checks": checks,
        "passed": all(row["passed"] for row in checks.values()),
    }


def repository_root() -> Path:
    for path in Path(__file__).resolve().parents:
        if (path / "docs/specs/brain.md").exists():
            return path
    raise RuntimeError("run evaluation from a source checkout")


def write_report(report: dict[str, object], directory: Path | None = None) -> Path:
    directory = directory if directory is not None else repository_root() / "eval-results/brain"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# Brain evaluation — toy-v0",
        "",
        "Synthetic model checks, not biological validation.",
        "",
        "| Check | Pass | Measurements |",
        "| --- | --- | --- |",
    ]
    for name, row in report["checks"].items():
        measurements = {
            key: value
            for key, value in row.items()
            if key != "passed" and not isinstance(value, (dict, list, tuple))
        }
        lines.append(f"| {name} | {row['passed']} | `{json.dumps(measurements)}` |")
    decoder = report["checks"].get("decoder", {})
    if decoder:
        lines.extend(["", "## Decoder", "", "| Model | Accuracy |", "| --- | ---: |"])
        for name, row in decoder.items():
            if isinstance(row, dict) and "accuracy" in row:
                lines.append(f"| {name} | {row['accuracy']:.2%} |")
        labels = decoder["labels"]
        for name, row in decoder.items():
            if not isinstance(row, dict) or "confusion_matrix" not in row:
                continue
            lines.extend(
                [
                    "",
                    f"### {name} confusion matrix",
                    "",
                    "| True / predicted | " + " | ".join(labels) + " |",
                    "| --- | " + " | ".join(["---:"] * len(labels)) + " |",
                ]
            )
            for label, counts in zip(labels, row["confusion_matrix"], strict=True):
                lines.append(f"| {label} | " + " | ".join(map(str, counts)) + " |")
    lines.extend(
        [
            "",
            "Decoder confusion matrices: rows = true, columns = predicted; labels in JSON.",
            "Shuffled controls preserve each projection's weights (including zeros).",
            "The decoder is frozen; three control seeds use the same held-out individuals.",
            "A 10 percentage-point average drop operationalizes 'large drop' for this toy model.",
        ]
    )
    (directory / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return directory


def main() -> None:
    report = run_evaluation()
    directory = write_report(report)
    print(f"Brain evaluation: {'PASS' if report['passed'] else 'FAIL'}; {directory}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
