from __future__ import annotations

from tsuyu_brain.connectome import DEFAULT_VERSION, load_circuit
from tsuyu_brain.decoder import default_decoder
from tsuyu_brain.learning import FlyState, new_fly_state
from tsuyu_brain.params import default_params


def test_promoted_default_preserves_explicit_legacy_states() -> None:
    assert DEFAULT_VERSION == "malecns-v1.0"
    state = new_fly_state(default_params())
    assert state.version == load_circuit("feeding").version == DEFAULT_VERSION
    assert default_decoder().version == DEFAULT_VERSION
    assert state.kc_mbon.shape == (200, 20)
    legacy = new_fly_state(default_params(), "toy-v0")
    assert FlyState.from_bytes(legacy.to_bytes()).version == "toy-v0"
    assert default_decoder("toy-v0").version == "toy-v0"
