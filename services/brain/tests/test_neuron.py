from __future__ import annotations

import torch
from tsuyu_brain.neuron import LIFPopulation, poisson_input


def test_threshold_reset_and_refractory() -> None:
    neurons = LIFPopulation(2, batch=3)
    assert not neurons.step(torch.zeros(3, 2)).any()
    assert neurons.step(torch.full((3, 2), 50.0)).all()
    assert (neurons.voltage == 0).all()
    for _ in range(4):
        assert not neurons.step(torch.full((3, 2), 50.0)).any()
    assert neurons.step(torch.full((3, 2), 50.0)).all()


def test_current_decay_and_leak() -> None:
    neurons = LIFPopulation(1, threshold=100.0)
    neurons.step(torch.tensor([[2.0]]))
    assert torch.allclose(neurons.voltage, torch.tensor([[0.05]]))
    neurons.step(torch.zeros(1, 1))
    assert 0 < neurons.current.item() < 2
    for _ in range(1000):
        neurons.step(torch.zeros(1, 1))
    assert neurons.voltage.item() < 1e-8


def test_poisson_seed_and_rate() -> None:
    rates = torch.full((100, 100), 1000.0)
    a = poisson_input(rates, torch.Generator().manual_seed(7))
    b = poisson_input(rates, torch.Generator().manual_seed(7))
    assert torch.equal(a, b)
    assert 0.37 < a.float().mean() < 0.42
    assert not poisson_input(rates * 0, torch.Generator()).any()
