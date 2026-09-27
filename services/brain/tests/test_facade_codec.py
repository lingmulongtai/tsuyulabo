from __future__ import annotations

import torch
from tsuyu_brain.api import BrainParams, FlyState, default_params, new_fly_state


def test_public_codec_round_trip() -> None:
    state = new_fly_state(default_params())
    restored = FlyState.from_bytes(state.to_bytes())
    assert restored.params == BrainParams(**state.params.to_dict())
    assert restored.version == state.version
    assert torch.allclose(restored.kc_mbon, state.kc_mbon, atol=0.001)
    restored.kc_mbon.zero_()
    assert state.kc_mbon.any()
