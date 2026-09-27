from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest
from tsuyu_worker.brain_adapter import (
    BrainSnapshot,
    BrainUnavailable,
    FakeBrainEngine,
    RealBrainEngine,
)
from tsuyulabo_api.services import shiori_brain as brain_adapter


def test_fake_is_deterministic_and_does_not_mutate() -> None:
    snapshot = BrainSnapshot("f", {"associations": {"banana": 0.5}})
    original = deepcopy(snapshot)
    assert FakeBrainEngine().run_odor_choice(snapshot, "banana", 20, 0) == {"toward": 15, "away": 5}
    assert snapshot == original


def test_real_adapter_decodes_without_replaying(monkeypatch: pytest.MonkeyPatch) -> None:
    def run(state: dict, cue: str, trials: int, seed: int) -> dict:
        state["mutated"] = True
        return {"toward": trials, "away": 0}

    api = SimpleNamespace(
        FlyState=SimpleNamespace(from_bytes=lambda _: {}),
        run_odor_choice=run,
    )
    monkeypatch.setattr(brain_adapter, "import_module", lambda _: api)
    snapshot = BrainSnapshot(
        "f", learned_weights=b"codec", training=[{"cue": "banana", "valence": "reward"}]
    )
    original = deepcopy(snapshot)
    assert RealBrainEngine().run_odor_choice(snapshot, "banana", 20, 4)["toward"] == 20
    assert snapshot == original


def test_missing_engine_fails_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> None:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(brain_adapter, "import_module", missing)
    with pytest.raises(BrainUnavailable):
        RealBrainEngine().run_odor_choice(BrainSnapshot("f"), "banana", 20, 0)
