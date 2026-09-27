from __future__ import annotations

import pytest
import torch
from tsuyu_brain.circuit import Circuit
from tsuyu_brain.connectome.malecns_normalization import normalize_mbon_inputs


def test_homeostasis_preserves_edges_signs_and_afferent_ratios() -> None:
    weights = torch.zeros(5, 5)
    weights[:2, 3:] = torch.tensor([[2.0, 0.0], [6.0, 4.0]])
    weights[2, 3:] = torch.tensor([-10.0, -20.0])
    circuit = Circuit(
        "olfaction_mb",
        {"KC": slice(0, 2), "APL": slice(2, 3), "MBON_ap": slice(3, 4), "MBON_av": slice(4, 5)},
        weights,
        torch.tensor([1, 1, -1, 1, 1]),
        (),
        ("MBON_ap", "MBON_av"),
    )
    normalized, info = normalize_mbon_inputs(circuit, torch.tensor([10, 10, 100, 0, 0.0]))
    assert torch.equal(normalized.weights[:2, 3:].sum(0), torch.tensor([40.0, 40.0]))
    assert normalized.weights[0, 3] / normalized.weights[1, 3] == pytest.approx(1 / 3)
    assert torch.equal(normalized.weights[2, 3:], torch.tensor([-1.0, -2.0]))
    assert torch.equal(normalized.weights.sign(), weights.sign())
    assert torch.equal(circuit.weights, weights)
    for projection, gains in info["projection_factors"].items():
        source, target = projection.split("->")
        assert torch.allclose(
            normalized.weights[circuit.groups[source], circuit.groups[target]],
            weights[circuit.groups[source], circuit.groups[target]] * torch.tensor(gains),
        )
    silent, _ = normalize_mbon_inputs(circuit, torch.zeros(5))
    assert torch.equal(silent.weights[2], weights[2])
    for budget in (0, -1, float("nan")):
        with pytest.raises(ValueError, match="budget"):
            normalize_mbon_inputs(circuit, torch.zeros(5), budget)
