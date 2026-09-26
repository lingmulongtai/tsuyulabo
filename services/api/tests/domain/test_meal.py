from __future__ import annotations

from random import Random

import pytest
from tsuyulabo_api.domain.puzzles import meal


def params(shapes: list[str], size: int = 8) -> dict:
    return {
        "rows": size,
        "cols": size,
        "hand_size": 3,
        "theme": "banana",
        "time_limit_ms": 30000,
        "pieces": [{"shape": s, "ingredient": "banana"} for s in shapes],
    }


def moves(cells: list[tuple[int, int, int]]) -> dict:
    return {
        "moves": [{"p": p, "r": r, "c": c, "t": i} for i, (p, r, c) in enumerate(cells)],
        "elapsed_ms": 30000,
    }


def test_intersection_and_combo() -> None:
    # Fill row 0 and column 0 without their intersection, then place the corner.
    p = params(["m1"] * 15)
    cells = [(i - 1, 0, i) for i in range(1, 8)]
    cells += [(i + 6, i, 0) for i in range(1, 8)] + [(14, 0, 0)]
    result = meal.verify(p, moves(cells))
    assert result.to_dict() == {
        "valid": True,
        "score": 540,
        "lines": 2,
        "max_combo": 1,
        "theme_cells": 15,
    }
    p = params(["i3h"] * 3, size=3)
    result = meal.verify(p, moves([(0, 0, 0), (1, 1, 0), (2, 2, 0)]))
    assert result.score == 594  # 9 cells + (100 + 150 + 200) + 9*15.
    assert result.max_combo == 3


@pytest.mark.parametrize(
    "cells,reason",
    [
        ([(3, 0, 0)], "not_in_hand"),
        ([(0, 0, 0), (0, 1, 0)], "already_placed"),
        ([(0, -1, 0)], "out_of_bounds"),
        ([(0, 0, 0), (1, 0, 0)], "cell_occupied"),
    ],
)
def test_invalid_moves(cells: list[tuple[int, int, int]], reason: str) -> None:
    assert meal.verify(params(["m1"] * 6), moves(cells)).reason == reason


def test_timing_hand_and_rolls() -> None:
    p = params(["m1"] * 6)
    assert meal.verify(p, moves([(2, 0, 0), (0, 0, 1), (1, 0, 2), (5, 0, 3)])).valid
    s = moves([(0, 0, 0)])
    s["moves"][0]["t"] = s["elapsed_ms"] = 31500
    assert meal.verify(p, s).valid
    s["moves"][0]["t"] = s["elapsed_ms"] = 31501
    assert meal.verify(p, s).reason == "time_exceeded"
    s["moves"][0]["t"] = -1
    assert meal.verify(p, s).reason == "non_monotonic_time"
    generated, secret = meal.generate(Random(1), {})
    assert len(generated["pieces"]) == 90 and not secret
    assert meal.generate(Random(1), {})[0] == generated
    assert meal.great_success_probability(99999, 7, 0.1) == 0.6
    assert meal.roll(Random(1), 6000, 4)["effects"]["growth"] == 180
