from __future__ import annotations

import torch
from tsuyu_brain.behavior import FEATURES, scenario_features, shuffled_wiring
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.learning import new_fly_state
from tsuyu_brain.params import default_params


def test_scenario_output_features() -> None:
    state = new_fly_state(default_params(), "toy-v0")
    for scenario, output in [
        ("sugar", "MN9"),
        ("looming", "DNp01"),
        ("light_left", "DNa02_L"),
        ("light_right", "DNa02_R"),
        ("antenna_touch", "aDN"),
    ]:
        values = scenario_features(state, scenario, batch=2, duration_ms=100)
        assert values.shape == (2, 8)
        assert values[:, FEATURES.index(output)].mean() > 0
    rest = scenario_features(state, "rest", duration_ms=100)
    walk = scenario_features(state, "walk", duration_ms=100)
    assert walk[:, 4] > rest[:, 4]


def test_shuffle_preserves_projection_distributions() -> None:
    circuit = load_circuit("olfaction_mb")
    before = circuit.weights.clone()
    control = shuffled_wiring(circuit, 0)
    assert not torch.equal(before, control.weights)
    assert torch.equal(before, circuit.weights)
    for source, target in circuit.projections:
        block = (circuit.groups[source], circuit.groups[target])
        assert torch.equal(
            before[block].flatten().sort().values, control.weights[block].flatten().sort().values
        )
