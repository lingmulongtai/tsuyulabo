from __future__ import annotations

from pathlib import Path

import torch
from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.npz_io import load_npz_circuit, save_circuit
from tsuyu_brain.params import default_params


def test_sparse_interchange(tmp_path: Path) -> None:
    circuit = load_circuit("feeding")
    path = tmp_path / "feeding.npz"
    save_circuit(circuit, path, {"source": "synthetic test fixture"})
    restored = load_npz_circuit(path)
    assert restored.groups == circuit.groups
    assert torch.equal(restored.weights, circuit.weights)
    assert torch.equal(restored.signs, circuit.signs)
    a = simulate(circuit, {"Gr64f": 1}, default_params(), duration_ms=50)
    b = simulate(restored, {"Gr64f": 1}, default_params(), duration_ms=50)
    assert torch.equal(a.neuron_rates, b.neuron_rates)
