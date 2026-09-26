from __future__ import annotations

from pathlib import Path

import torch
from tsuyu_brain.decoder.dataset import Dataset, split_dataset
from tsuyu_brain.decoder.model import Decoder, evaluate_decoder, train_decoder


def test_group_split_and_models(tmp_path: Path) -> None:
    generator = torch.Generator().manual_seed(1)
    x = torch.randn(90, 8, generator=generator)
    y = (x[:, 0] > 0).long()
    data = Dataset(x, y, torch.arange(90) // 9)
    train, test = split_dataset(data)
    assert not set(train.individuals.tolist()) & set(test.individuals.tolist())
    before = torch.random.get_rng_state().clone()
    for kind in ("logistic", "mlp"):
        model = train_decoder(train, kind, epochs=100)
        metrics = evaluate_decoder(model, test)
        assert metrics["accuracy"] > 0.85
        assert sum(map(sum, metrics["confusion_matrix"])) == len(test.labels)
        path = tmp_path / f"{kind}.pt"
        model.save(path)
        assert path.stat().st_size < 200_000
        assert torch.equal(model.predict(x), Decoder.load(path).predict(x))
    assert torch.equal(before, torch.random.get_rng_state())
