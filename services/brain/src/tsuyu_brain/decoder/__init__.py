"""Trained behavior decoder, lazily loaded once per process."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from tsuyu_brain.decoder.model import Decoder


@lru_cache(maxsize=1)
def default_decoder() -> Decoder:
    checkpoint = Path(__file__).parent / "weights" / "toy-v0.pt"
    if checkpoint.exists():
        return Decoder.load(checkpoint)
    from tsuyu_brain.decoder.dataset import generate_dataset, split_dataset
    from tsuyu_brain.decoder.model import train_decoder

    train, _ = split_dataset(generate_dataset())
    return train_decoder(train, "mlp")
