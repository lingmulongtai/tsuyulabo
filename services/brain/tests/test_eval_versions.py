from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch
from tsuyu_brain import eval as brain_eval
from tsuyu_brain.connectome import DEFAULT_VERSION


@pytest.fixture(autouse=True)
def single_thread() -> Iterator[None]:
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def test_versioned_report_and_failed_cli_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = {
        "connectome": "malecns-v1.0",
        "checks": {"trait_bias": {"passed": False, "p_one_sided": None}},
        "passed": False,
    }
    versions = []

    def evaluate(version: str) -> dict[str, object]:
        versions.append(version)
        return report

    monkeypatch.setattr(brain_eval, "run_evaluation", evaluate)
    monkeypatch.setattr(
        "sys.argv", ["eval", "--version", "malecns-v1.0", "--output", str(tmp_path)]
    )
    with pytest.raises(SystemExit) as error:
        brain_eval.main()
    assert error.value.code == 1
    assert versions == ["malecns-v1.0"]
    saved = json.loads((tmp_path / "report-malecns.json").read_text())
    assert saved["connectome"] == "malecns-v1.0"
    assert saved["checks"]["trait_bias"]["p_one_sided"] is None
    assert "malecns-v1.0" in (tmp_path / "report-malecns.md").read_text(encoding="utf8")
    assert not (tmp_path / "report.json").exists()


@pytest.mark.eval
def test_measured_sanity_gates_report_failures_honestly() -> None:
    checks = brain_eval.sanity_metrics("malecns-v1.0")
    assert checks["sugar_mn9"]["passed"], checks
    assert checks["looming_dnp01"]["passed"], checks
    assert checks["bitter_suppression"]["passed"] == (
        checks["bitter_suppression"]["mixed_hz"] < 0.5 * checks["bitter_suppression"]["sugar_hz"]
    )
    # The extracted MB fails the bidirectional PI gate. Keep the game default unchanged.
    assert not checks["learning"]["passed"], checks
    assert DEFAULT_VERSION == "toy-v0"
    assert all(isinstance(row["passed"], bool) for row in checks.values())
    print(json.dumps(checks))


@pytest.mark.eval
def test_missing_visual_path_does_not_fake_trait_significance() -> None:
    metrics = brain_eval.trait_metrics(version="malecns-v1.0")
    assert metrics["passed"] is False
    assert metrics["p_one_sided"] is None
    assert metrics["wild_mean_right_fraction"] == metrics["trait_mean_right_fraction"] == 0
