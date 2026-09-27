from __future__ import annotations

from collections.abc import Iterator

import pytest
import torch
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.stimuli import cue_stimulus
from tsuyu_brain.learning import FlyState, apply_training, learned_circuit, new_fly_state
from tsuyu_brain.params import default_params


@pytest.fixture(autouse=True)
def single_thread() -> Iterator[None]:
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def test_measured_state_roundtrip_and_unmodified_initial_wiring() -> None:
    circuit = load_circuit("olfaction_mb", "malecns-v1.0")
    state = new_fly_state(default_params(), circuit.version)
    assert state.kc_mbon.shape == (200, 20)
    assert torch.equal(learned_circuit(state).weights, circuit.weights)
    restored = FlyState.from_bytes(state.to_bytes())
    assert restored.version == state.version
    assert torch.allclose(restored.kc_mbon, state.kc_mbon, rtol=0.0005, atol=0.0001)
    assert restored.to_bytes() == state.to_bytes()
    with pytest.raises(ValueError, match="shape"):
        FlyState(default_params(), torch.ones(200, 2), circuit.version)


@pytest.mark.parametrize("cue", ["banana", "apple_vinegar", "yeast", "grape", "blue_light"])
def test_real_cues_have_population_sized_inputs(cue: str) -> None:
    circuit = load_circuit("olfaction_mb", "malecns-v1.0")
    stimulus = cue_stimulus(cue, circuit.version)
    assert set(stimulus) <= set(circuit.input_groups)
    for group, value in stimulus.items():
        if isinstance(value, torch.Tensor):
            assert len(value) == circuit.groups[group].stop - circuit.groups[group].start
    with pytest.raises(ValueError, match="unsupported"):
        cue_stimulus(cue, "unknown")


@pytest.mark.eval
@pytest.mark.parametrize("valence,target", [("reward", "MBON_av"), ("punish", "MBON_ap")])
def test_measured_learning_depresses_only_existing_target_edges(valence: str, target: str) -> None:
    circuit = load_circuit("olfaction_mb", "malecns-v1.0")
    initial = new_fly_state(default_params(), circuit.version)
    before = initial.to_bytes()
    updated, pi = apply_training(initial, "banana", valence, 1, 9)
    repeated, _ = apply_training(initial, "banana", valence, 1, 9)
    assert -1 <= pi <= 1
    assert initial.to_bytes() == before
    assert torch.equal(updated.kc_mbon, repeated.kc_mbon)
    changed = learned_circuit(updated).weights != circuit.weights
    allowed = torch.zeros_like(changed)
    allowed[circuit.groups["KC"], circuit.groups[target]] = True
    assert not (changed & ~allowed).any()
    assert changed.any()
    assert (updated.kc_mbon <= initial.kc_mbon).all()
    assert not (updated.kc_mbon[initial.kc_mbon == 0] != 0).any()
