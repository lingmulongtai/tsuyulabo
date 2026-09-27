"""Trained behavior decoder, lazily loaded once per process."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from tsuyu_brain.connectome import DEFAULT_VERSION, VERSIONS
from tsuyu_brain.decoder.model import Decoder


@lru_cache(maxsize=2)
def default_decoder(version: str = DEFAULT_VERSION) -> Decoder:
    if version not in VERSIONS:
        raise ValueError(f"unsupported decoder version: {version}")
    checkpoint = Path(__file__).parent / "weights" / f"{version}.pt"
    if checkpoint.exists():
        return Decoder.load(checkpoint, version=version)
    from tsuyu_brain.decoder.dataset import generate_dataset, split_dataset
    from tsuyu_brain.decoder.model import train_decoder

    train, _ = split_dataset(generate_dataset(version=version))
    return train_decoder(train, "mlp")
