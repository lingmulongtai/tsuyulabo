from __future__ import annotations

import pytest
import torch
from tsuyu_brain.circuit import Circuit, simulate
from tsuyu_brain.params import default_params


def test_simulation_shapes_windows_and_seed() -> None:
    circuit = Circuit(
        "test",
        {"input": slice(0, 1), "output": slice(1, 2)},
        torch.tensor([[0.0, 12.0], [0.0, 0.0]]),
        torch.ones(2),
        ("input",),
        ("output",),
    )
    a = simulate(circuit, {"input": 1}, default_params(), 125, 3, 4, record_spikes=True)
    b = simulate(circuit, {"input": 1}, default_params(), 125, 3, 4, record_spikes=True)
    assert a.spikes.shape == (250, 3, 2)
    assert a.rates["output"].shape == (3, 3)
    assert a.window_ms.tolist() == [50, 50, 25]
    assert torch.equal(a.spikes, b.spikes)
    assert a.neuron_rates[:, 1].mean() > 0
    assert torch.allclose((a.rates["output"] * a.window_ms).sum(1) / 125, a.neuron_rates[:, 1])
    with pytest.raises(ValueError):
        simulate(circuit, {"typo": 1}, default_params())
    with pytest.raises(ValueError):
        simulate(circuit, {}, default_params(), duration_ms=0.1)
