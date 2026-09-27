"""Compact float16 state deltas bound to the exact versioned baseline wiring."""

from __future__ import annotations

import base64
import hashlib
import zlib
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

import numpy as np
import torch
from torch import Tensor

from tsuyu_brain.connectome import load_circuit


@lru_cache(maxsize=2)
def baseline(version: str) -> tuple[bytes, str]:
    circuit = load_circuit("olfaction_mb", version)
    weights = torch.cat(
        [
            circuit.weights[circuit.groups["KC"], circuit.groups[group]]
            for group in ("MBON_ap", "MBON_av")
        ],
        dim=1,
    ).abs()
    raw = weights.numpy().astype("<f2").tobytes()
    return raw, hashlib.sha256(raw).hexdigest()


def xor_bytes(left: bytes, right: bytes) -> bytes:
    if len(left) != len(right):
        raise ValueError("state delta does not match baseline shape")
    return np.bitwise_xor(
        np.frombuffer(left, dtype="u1"), np.frombuffer(right, dtype="u1")
    ).tobytes()


def encode_weights(weights: Tensor, version: str) -> dict[str, str]:
    raw = weights.detach().cpu().numpy().astype("<f2").tobytes()
    if version == "toy-v0":
        return {"kc_mbon_f16": base64.b64encode(raw).decode("ascii")}
    initial, digest = baseline(version)
    delta = zlib.compress(xor_bytes(raw, initial), level=9)
    return {
        "kc_mbon_delta_f16_zlib": base64.b64encode(delta).decode("ascii"),
        "kc_mbon_base_sha256": digest,
    }


def decode_weights(data: Mapping[str, Any], shape: tuple[int, int]) -> Tensor:
    expected = shape[0] * shape[1] * 2
    if "kc_mbon_f16" in data:
        # Read old toy and experimental measured states without replay or migration.
        raw = base64.b64decode(data["kc_mbon_f16"], validate=True)
    else:
        initial, digest = baseline(data["version"])
        if data.get("kc_mbon_base_sha256") != digest:
            raise ValueError("state baseline checksum mismatch")
        encoded = base64.b64decode(data["kc_mbon_delta_f16_zlib"], validate=True)
        stream = zlib.decompressobj()
        try:
            delta = stream.decompress(encoded, expected + 1)
        except zlib.error as error:
            raise ValueError("invalid compressed state delta") from error
        if len(delta) != expected or not stream.eof or stream.unused_data:
            raise ValueError("unexpected size or trailing data in compressed state")
        raw = xor_bytes(delta, initial)
    if len(raw) != expected:
        raise ValueError("unexpected number of float16 weights for state version")
    return torch.from_numpy(np.frombuffer(raw, dtype="<f2").astype("float32")).reshape(*shape)
