"""Versioned registry. Returned tensors must be treated as read-only."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from tsuyu_brain.circuit import Circuit
from tsuyu_brain.connectome.toy_v0 import build_circuit

DEFAULT_VERSION = "malecns-v1.0"
VERSIONS = ("toy-v0", DEFAULT_VERSION)


@lru_cache(maxsize=10)
def load_circuit(name: str, version: str = DEFAULT_VERSION) -> Circuit:
    if version == "toy-v0":
        return build_circuit(name)
    if version == "malecns-v1.0":
        from tsuyu_brain.connectome.malecns import verified_path
        from tsuyu_brain.connectome.npz_io import load_npz_circuit

        return load_npz_circuit(verified_path(name))
    raise ValueError(f"unsupported connectome version: {version}")


def data_directory() -> Path:
    return Path(__file__).parent / "malecns_v1"
