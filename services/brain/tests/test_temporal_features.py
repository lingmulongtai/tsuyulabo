from __future__ import annotations

from pathlib import Path

import pytest
import torch
from tsuyu_brain.circuit import SimResult
from tsuyu_brain.decoder.dataset import Dataset
from tsuyu_brain.decoder.features import window_rates
from tsuyu_brain.decoder.model import train_decoder


def test_partial_windows_preserve_total_rate() -> None:
    result = SimResult(
        {"output": torch.tensor([[2.0, 8.0, 20.0]])},
        torch.zeros(1, 1),
        torch.tensor([50.0, 50.0, 20.0]),
    )
    rebinned = window_rates(result, "output")
    assert torch.equal(rebinned, torch.tensor([[2.0, 2.0, 5.0, 8.0, 8.0, 20.0]]))
    assert rebinned.mean() == (result.rates["output"] * result.window_ms).sum() / 120


def test_temporal_schema_uses_same_classifier_and_cannot_mislabel_checkpoint(
    tmp_path: Path,
) -> None:
    generator = torch.Generator().manual_seed(5)
    x = torch.randn(32, 68, generator=generator)
    data = Dataset(x, (x[:, 0] > 0).long(), torch.arange(32))
    model = train_decoder(data, "mlp", epochs=2)
    assert model.weights[0].shape == (68, 16)
    assert model.predict(x).shape == (32, 9)
    with pytest.raises(ValueError, match="schema"):
        model.save(tmp_path / "wrong-schema.pt")
    assert not (tmp_path / "wrong-schema.pt").exists()
