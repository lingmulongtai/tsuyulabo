"""Versioned registry. Returned tensors must be treated as read-only."""

from __future__ import annotations

from functools import lru_cache

from tsuyu_brain.circuit import Circuit
from tsuyu_brain.connectome.toy_v0 import build_circuit


@lru_cache(maxsize=5)
def load_circuit(name: str, version: str = "toy-v0") -> Circuit:
    if version != "toy-v0":
        raise ValueError(f"unsupported connectome version: {version}")
    return build_circuit(name)
