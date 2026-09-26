from __future__ import annotations

import pytest
import torch
from tsuyu_brain.connectome.toy_v0 import CUES
from tsuyu_brain.individuality import generate_individual
from tsuyu_brain.learning import FlyState, apply_training, new_fly_state, preference_index
from tsuyu_brain.params import default_params


@pytest.mark.parametrize("cue", CUES)
def test_reward_and_punishment(cue: str) -> None:
    initial = new_fly_state(default_params())
    before = initial.to_bytes()
    reward, punish = initial, initial
    for seed in range(3):
        reward, _ = apply_training(reward, cue, "reward", 1, seed)
        punish, _ = apply_training(punish, cue, "punish", 1, seed)
    assert preference_index(reward, cue, 42, 4) >= 0.3
    assert preference_index(punish, cue, 42, 4) <= -0.3
    assert initial.to_bytes() == before
    assert torch.equal(reward.kc_mbon[:, 0], initial.kc_mbon[:, 0])
    assert torch.equal(punish.kc_mbon[:, 1], initial.kc_mbon[:, 1])


def test_serialization_size_and_seed() -> None:
    state = new_fly_state(generate_individual(["keen_nose"], "f", 0))
    trained, value = apply_training(state, "banana", "reward", 0.7, 8)
    repeated, other = apply_training(state, "banana", "reward", 0.7, 8)
    assert torch.equal(trained.kc_mbon, repeated.kc_mbon) and value == other
    payload = trained.to_bytes()
    assert len(payload) < 4096
    restored = FlyState.from_bytes(payload)
    assert restored.params == trained.params
    assert torch.allclose(restored.kc_mbon, trained.kc_mbon, atol=0.0003)
    assert restored.to_bytes() == payload


def test_zero_strength_and_invalid_training() -> None:
    state = new_fly_state(default_params())
    unchanged, _ = apply_training(state, "banana", "reward", 0, 0)
    assert torch.equal(unchanged.kc_mbon, state.kc_mbon)
    for cue, valence, strength in [
        ("unknown", "reward", 1),
        ("banana", "other", 1),
        ("banana", "reward", -1),
    ]:
        with pytest.raises(ValueError):
            apply_training(state, cue, valence, strength, 0)
