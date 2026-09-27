from __future__ import annotations

import base64
import json
import zlib
from dataclasses import replace

import pytest
import torch
from tsuyu_brain.learning import FlyState, new_fly_state
from tsuyu_brain.params import default_params


def test_measured_delta_is_compact_and_preserves_float16_bits() -> None:
    state = new_fly_state(default_params(), "malecns-v1.0")
    weights = state.kc_mbon.clone()
    weights[:20] *= 0.75
    state = replace(state, kc_mbon=weights)
    payload = state.to_bytes()
    assert len(payload) < 3000
    restored = FlyState.from_bytes(payload)
    assert torch.equal(restored.kc_mbon, weights.half().float())
    assert restored.to_bytes() == payload
    data = json.loads(payload)
    data["kc_mbon_base_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="baseline checksum"):
        FlyState.from_bytes(json.dumps(data).encode())


@pytest.mark.parametrize("version", ["toy-v0", "malecns-v1.0"])
def test_legacy_dense_state_remains_readable(version: str) -> None:
    state = new_fly_state(default_params(), version)
    raw = state.kc_mbon.numpy().astype("<f2").tobytes()
    payload = json.dumps(
        {
            "version": version,
            "params": state.params.to_dict(),
            "kc_mbon_f16": base64.b64encode(raw).decode(),
        }
    ).encode()
    restored = FlyState.from_bytes(payload)
    assert restored.version == version
    assert torch.equal(restored.kc_mbon, state.kc_mbon.half().float())


@pytest.mark.parametrize("raw", [b"short", bytes(8001)])
def test_compressed_state_rejects_wrong_decompressed_size(raw: bytes) -> None:
    data = json.loads(new_fly_state(default_params(), "malecns-v1.0").to_bytes())
    data["kc_mbon_delta_f16_zlib"] = base64.b64encode(zlib.compress(raw)).decode()
    with pytest.raises(ValueError, match="size"):
        FlyState.from_bytes(json.dumps(data).encode())
