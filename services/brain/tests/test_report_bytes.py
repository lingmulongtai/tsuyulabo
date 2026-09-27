from __future__ import annotations

import json
from pathlib import Path

from tsuyu_brain.eval import write_report


def test_reports_use_lf_and_preserve_normalization_provenance(tmp_path: Path) -> None:
    report = {
        "connectome": "malecns-v1.0",
        "checks": {"learning": {"passed": True, "baseline_pi": 0.08}},
        "calibration": {"normalization": {"kc_budget": 40}},
        "passed": True,
    }
    write_report(report, tmp_path)
    for suffix in ("json", "md"):
        raw = (tmp_path / f"report-malecns.{suffix}").read_bytes()
        assert b"\r\n" not in raw
        assert raw.endswith(b"\n")
    assert json.loads((tmp_path / "report-malecns.json").read_text()) == report
