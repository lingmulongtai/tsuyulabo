from __future__ import annotations

import torch
from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.toy_v0 import CIRCUIT_NAMES, build_circuit
from tsuyu_brain.params import default_params


def test_topologies() -> None:
    for name in CIRCUIT_NAMES:
        circuit = load_circuit(name, "toy-v0")
        assert torch.equal(circuit.weights, build_circuit(name).weights)
        assert circuit.version == "toy-v0"
    mb = load_circuit("olfaction_mb", "toy-v0")
    assert (mb.weights[mb.groups["PN"], mb.groups["KC"]].count_nonzero(dim=0) == 6).all()
    assert mb.groups["KC"].stop - mb.groups["KC"].start == 200
    assert (mb.weights[mb.groups["APL"]] <= 0).all()


def test_spec_sanity() -> None:
    params = default_params()
    feeding = load_circuit("feeding")
    rest = simulate(feeding, {}, params, batch=4).rates["MN9"].mean()
    sugar = simulate(feeding, {"Gr64f": 1}, params, batch=4).rates["MN9"].mean()
    bitter = simulate(feeding, {"Gr64f": 1, "Gr66a": 1}, params, batch=4).rates["MN9"].mean()
    assert sugar > 0 and sugar >= 5 * rest
    assert bitter < 0.5 * sugar
    escape = load_circuit("escape")
    assert simulate(escape, {"LPLC2": 1, "LC4": 1}, params).rates["DNp01"].mean() > 0
    assert simulate(escape, {}, params).rates["DNp01"].sum() == 0
    steering = simulate(load_circuit("steering"), {}, params)
    assert steering.rates["walking_DN"].mean() > 0
