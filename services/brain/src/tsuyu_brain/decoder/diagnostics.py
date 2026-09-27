"""Describe response collisions without fitting or evaluating a classifier."""

from __future__ import annotations

import torch

from tsuyu_brain.behavior import LABELS
from tsuyu_brain.decoder.dataset import Dataset


def feature_diagnostics(data: Dataset) -> dict[str, object]:
    """Empirical ceiling: identical feature vectors must receive one prediction.

    This is a bound on this finite sample, not a population accuracy estimate.
    Use development data to diagnose ambiguity; never select changes on test data.
    """
    _, inverse = data.features.unique(dim=0, return_inverse=True)
    counts = torch.bincount(
        inverse * len(LABELS) + data.labels,
        minlength=(int(inverse.max()) + 1) * len(LABELS),
    ).reshape(-1, len(LABELS))
    correct = int(counts.max(dim=1).values.sum())
    return {
        "rows": len(data.labels),
        "unavoidable_errors_from_identical_features": len(data.labels) - correct,
        "empirical_accuracy_ceiling": correct / len(data.labels),
        "zero_feature_rows_by_label": {
            label: int(((data.features == 0).all(1) & (data.labels == index)).sum())
            for index, label in enumerate(LABELS)
        },
    }
