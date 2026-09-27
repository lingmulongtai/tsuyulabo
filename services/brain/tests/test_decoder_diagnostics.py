from __future__ import annotations

import torch
from tsuyu_brain.decoder.dataset import Dataset
from tsuyu_brain.decoder.diagnostics import feature_diagnostics


def test_identical_features_bound_accuracy_even_with_unlimited_capacity() -> None:
    data = Dataset(
        torch.tensor([[0.0, 0], [0.0, 0], [0.0, 0], [1.0, 0]]),
        torch.tensor([0, 0, 4, 4]),
        torch.tensor([0, 1, 2, 3]),
    )
    result = feature_diagnostics(data)
    assert result["unavoidable_errors_from_identical_features"] == 1
    assert result["empirical_accuracy_ceiling"] == 0.75
    assert result["zero_feature_rows_by_label"]["rest"] == 2
    assert result["zero_feature_rows_by_label"]["feed"] == 1
