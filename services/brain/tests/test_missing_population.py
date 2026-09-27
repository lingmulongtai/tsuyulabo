from __future__ import annotations

import torch
from tsuyu_brain.circuit import Circuit, simulate
from tsuyu_brain.params import default_params


def test_missing_population_remains_empty_and_silent() -> None:
    circuit = Circuit(
        "incomplete",
        {"sensory": slice(0, 0), "motor": slice(0, 1)},
        torch.zeros(1, 1),
        torch.ones(1),
        ("sensory",),
        ("motor",),
    )
    result = simulate(circuit, {"sensory": 1}, default_params(), duration_ms=5, batch=2)
    assert result.neuron_rates.shape == (2, 1)
    assert torch.equal(result.rates["sensory"], torch.zeros(2, 1))
    assert torch.equal(result.rates["motor"], torch.zeros(2, 1))
