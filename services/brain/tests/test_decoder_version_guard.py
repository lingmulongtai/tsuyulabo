from __future__ import annotations

from pathlib import Path

import pytest
import torch
from tsuyu_brain.api import predict_behavior
from tsuyu_brain.decoder import default_decoder
from tsuyu_brain.decoder.dataset import Dataset, split_dataset
from tsuyu_brain.decoder.model import Decoder, checkpoint_features, train_decoder
from tsuyu_brain.learning import new_fly_state
from tsuyu_brain.params import default_params


@pytest.mark.parametrize("version", ["toy-v0", "malecns-v1.0"])
def test_checkpoint_roundtrip_binds_version_and_schema(tmp_path: Path, version: str) -> None:
    width = len(checkpoint_features(version))
    data = Dataset(
        torch.zeros(12, width), torch.zeros(12, dtype=torch.long), torch.arange(12), version
    )
    train, test = split_dataset(data)
    assert train.version == test.version == version
    model = train_decoder(train, "mlp", epochs=1)
    path = tmp_path / "decoder.pt"
    model.save(path)
    restored = Decoder.load(path, version=version)
    assert restored.version == version
    assert torch.equal(restored.predict(data.features), model.predict(data.features))
    other = "toy-v0" if version == "malecns-v1.0" else "malecns-v1.0"
    with pytest.raises(ValueError, match="incompatible"):
        Decoder.load(path, version=other)


@pytest.mark.parametrize("version", ["toy-v0", "malecns-v1.0"])
def test_game_decoder_loads_checkpoint_matching_persisted_state(version: str) -> None:
    state = new_fly_state(default_params(), version)
    model = default_decoder(version)
    assert model.version == version
    assert model.mean.numel() == len(checkpoint_features(version))
    result = predict_behavior(state, "sugar")
    assert max(result, key=result.get) == "feed"
    assert sum(result.values()) == pytest.approx(1)
