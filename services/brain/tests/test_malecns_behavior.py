from __future__ import annotations

from collections.abc import Iterator

import pytest
import torch
from tsuyu_brain.behavior import scenario_features, shuffled_wiring
from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.toy_v0 import CIRCUIT_NAMES
from tsuyu_brain.learning import new_fly_state
from tsuyu_brain.params import default_params


@pytest.fixture(autouse=True)
def single_thread() -> Iterator[None]:
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


@pytest.mark.parametrize("name", CIRCUIT_NAMES)
def test_shuffle_preserves_mixed_group_signs_and_distributions(name: str) -> None:
    circuit = load_circuit(name, "malecns-v1.0")
    control = shuffled_wiring(circuit, 41)
    assert (control.weights * circuit.signs[:, None] >= 0).all()
    for source, target in circuit.projections:
        a, b = circuit.groups[source], circuit.groups[target]
        for sign in circuit.signs[a].unique():
            rows = circuit.signs[a] == sign
            original = circuit.weights[a, b][rows].flatten().sort().values
            shuffled = control.weights[a, b][rows].flatten().sort().values
            assert torch.equal(original, shuffled)


def test_scenarios_use_state_connectome_version() -> None:
    state = new_fly_state(default_params(), "malecns-v1.0")
    features = scenario_features(state, "sugar", batch=2, seed=19)
    expected = (
        simulate(
            load_circuit("feeding", state.version), {"Gr64f": 1}, state.params, batch=2, seed=19
        )
        .rates["MN9"]
        .mean(1)
    )
    assert torch.equal(features[:, 0], expected)
    assert features.shape == (2, 68)
    assert torch.isfinite(features).all()
    assert torch.allclose(features[:, 8:14].mean(1), expected)
    # Signed contrasts are neural outputs, never scenario-label indicators.
    assert torch.equal(features[:, 56:62], features[:, 26:32] - features[:, 20:26])
    assert torch.equal(features[:, 62:68], features[:, 44:50] - features[:, 50:56])
