from __future__ import annotations

import pytest
import torch
from tsuyu_brain.circuit import Circuit

pytest.importorskip("pandas")
import pandas as pd
from tsuyu_brain.connectome.malecns_selection import Selection
from tsuyu_brain.connectome.malecns_visual import add_visual_relays, normalize_steering


def test_visual_paths_keep_complete_measured_pairs_deterministically() -> None:
    rows = pd.DataFrame({"bodyId": range(6), "type": list("abcdef"), "sign": 1})
    selection = Selection(
        "steering",
        {"photo": rows.iloc[:1], "DNa02_L": rows.iloc[1:2], "DNa02_R": rows.iloc[:0]},
        ("photo",),
        ("DNa02_L", "DNa02_R"),
        {},
    )
    ends = pd.DataFrame(
        {"body_pre": [0, 0, 3, 5], "body_post": [2, 4, 1, 1], "weight": [20, 20, 20, 20]}
    )
    middle = pd.DataFrame({"body_pre": [2, 4], "body_post": [3, 5], "weight": [10, 9]})
    chosen = add_visual_relays(selection, rows, ends, middle, budget=2)
    assert chosen.groups["visual_relay"].bodyId.tolist() == [2, 3]
    repeated = add_visual_relays(selection, rows.iloc[::-1], ends, middle.iloc[::-1], budget=2)
    assert repeated.groups["visual_relay"].bodyId.tolist() == [2, 3]
    assert add_visual_relays(selection, rows, ends, middle, budget=1).groups["visual_relay"].empty
    rows.loc[2, "sign"] = float("nan")
    assert add_visual_relays(selection, rows, ends, middle, budget=2).groups[
        "visual_relay"
    ].bodyId.tolist() == [4, 5]


def test_steering_homeostasis_preserves_missing_edges_and_signs() -> None:
    weights = torch.tensor([[0, -2, -4, 0], [0, 0, 3, 1], [0, 0, 0, 0], [0, 0, 0, 0.0]])
    circuit = Circuit(
        "steering",
        {
            "photo": slice(0, 1),
            "visual_relay": slice(1, 2),
            "DNa02_L": slice(2, 3),
            "DNa02_R": slice(3, 4),
        },
        weights,
        torch.tensor([-1, 1, 1, 1]),
        ("photo",),
        ("DNa02_L", "DNa02_R"),
    )
    normalized, info = normalize_steering(circuit)
    assert torch.equal(normalized.weights.sign(), circuit.weights.sign())
    for sign in (-1, 1):
        mask = circuit.signs == sign
        assert torch.equal(
            normalized.weights[mask],
            circuit.weights[mask] * torch.tensor(info["source_sign_factors"][str(sign)]),
        )
    assert normalized.tonic == {"visual_relay": 1.15, "DNa02_L": 1.15, "DNa02_R": 1.15}
    assert not circuit.tonic
