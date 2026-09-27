from __future__ import annotations

import pytest
import torch
from tsuyulabo_api.brain_adapter import BrainAdapter


def test_real_codec_preserves_learning_without_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    brain = BrainAdapter()
    initial = brain.new()
    learned, value = brain.train(initial, "banana", "reward", 1, 1)
    assert value > 0
    before = brain.restore(learned).kc_mbon.clone()

    def no_replay(*args: object, **kwargs: object) -> None:
        pytest.fail("stored states must not replay training")

    monkeypatch.setattr(brain.api, "apply_training", no_replay)
    adult, params = brain.eclose(learned, ["brave", "glutton"], "f", 42)
    assert params == brain.restore(adult).params.to_dict()
    assert torch.equal(brain.restore(adult).kc_mbon, before)
    assert len(brain.restore(adult).to_bytes()) < 3000
    assert sum(brain.experiment(adult, "banana", 20, 4).values()) == 20
    assert initial["training"] == []
