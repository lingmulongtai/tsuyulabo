from __future__ import annotations

from pathlib import Path

import pytest
import torch
from tsuyu_brain import eval as brain_eval
from tsuyu_brain.decoder.dataset import Dataset


def test_evaluation_keeps_validation_and_test_out_of_fitting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = Dataset(torch.zeros(16, 8), torch.zeros(16, dtype=torch.long), torch.arange(16))
    training_ids: list[set[int]] = []
    controls: list[int | None] = []

    def generate(**kwargs: object) -> Dataset:
        controls.append(kwargs.get("shuffle_seed"))
        return data

    def train(rows: Dataset, kind: str) -> set[int]:
        ids = set(rows.individuals.tolist())
        training_ids.append(ids)
        return ids

    def evaluate(model: set[int], rows: Dataset) -> dict[str, object]:
        assert not model.intersection(rows.individuals.tolist())
        return {"accuracy": 1.0, "confusion_matrix": [[1] * 9] * 9}

    monkeypatch.setattr(brain_eval, "generate_dataset", generate)
    monkeypatch.setattr(brain_eval, "train_decoder", train)
    monkeypatch.setattr(brain_eval, "evaluate_decoder", evaluate)
    result = brain_eval.decoder_metrics("malecns-v1.0")
    assert training_ids[:2] == [{0, 3, 7, 8, 9, 11, 12, 13, 15}] * 2
    assert training_ids[2:] == [{0, 1, 2, 3, 7, 8, 9, 11, 12, 13, 14, 15}] * 2
    assert controls == [None, 41, 42, 43]
    assert result["protocol"]["test_individuals"] == [4, 5, 6, 10]
    brain_eval.write_report({"connectome": "malecns-v1.0", "checks": {"decoder": result}}, tmp_path)
    report = (tmp_path / "report-malecns.md").read_text(encoding="utf8")
    assert "Development fit: [0, 3, 7, 8, 9, 11, 12, 13, 15]" in report
    assert "validation: [1, 2, 14]" in report
    assert "test: [4, 5, 6, 10]" in report
    assert "empirical_accuracy_ceiling" in report
