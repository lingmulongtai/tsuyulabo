from __future__ import annotations

import json
import runpy
from collections import Counter
from pathlib import Path

import pytest
from tsuyulabo_api.domain.constants import REASON_CODES
from tsuyulabo_api.domain.puzzles import cleaning, meal, temperature, training

ROOT = Path(__file__).resolve().parents[4]
FILES = sorted((ROOT / "packages/fixtures/puzzles").glob("*/*.json"))
VERIFIERS = {
    "meal": meal.verify,
    "training": training.verify,
    "cleaning": cleaning.verify,
    "temperature": temperature.verify,
}


@pytest.mark.parametrize("path", FILES, ids=[f"{p.parent.name}/{p.stem}" for p in FILES])
def test_shared_fixture(path: Path) -> None:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    actual = VERIFIERS[fixture["kind"]](fixture["params"], fixture["submission"]).to_dict()
    assert actual == fixture["expected"]


def test_coverage_and_reproducibility() -> None:
    counts: Counter = Counter()
    reasons = set()
    for path in FILES:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        counts[fixture["kind"], fixture["expected"]["valid"]] += 1
        if not fixture["expected"]["valid"]:
            reasons.add(fixture["expected"]["reason"])
    for kind in VERIFIERS:
        assert counts[kind, True] >= 6
        assert counts[kind, False] >= 6
    assert reasons == REASON_CODES
    generator = runpy.run_path(str(ROOT / "services/api/scripts/gen_puzzle_fixtures.py"))
    generated = generator["build"]()
    assert len(generated) == len(FILES)
    for name, fixture in generated:
        path = ROOT / "packages/fixtures/puzzles" / fixture["kind"] / f"{name}.json"
        assert json.loads(path.read_text(encoding="utf-8")) == fixture
