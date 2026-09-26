from __future__ import annotations

from pathlib import Path

import pytest
from tsuyu_brain.eval import decoder_metrics, sanity_metrics, trait_metrics, write_report


@pytest.mark.eval
def test_statistical_trait_effect() -> None:
    assert trait_metrics()["passed"]


@pytest.mark.eval
def test_decoder_accuracy_and_shuffled_control() -> None:
    metrics = decoder_metrics()
    assert metrics["passed"], metrics


@pytest.mark.eval
def test_spec_evaluation_and_report(tmp_path: Path) -> None:
    checks = sanity_metrics()
    assert all(row["passed"] for row in checks.values())
    write_report({"checks": checks, "passed": True}, tmp_path)
    assert (tmp_path / "report.json").exists()
    assert "sugar_mn9" in (tmp_path / "report.md").read_text(encoding="utf-8")
