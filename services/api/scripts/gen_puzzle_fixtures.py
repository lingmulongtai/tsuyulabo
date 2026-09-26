"""Generate shared fixtures from hand-calculated assertions, then verify domain parity.

Run from the root: .\\.tools\\uv.exe run python services/api/scripts/gen_puzzle_fixtures.py
Use --check to compare checked-in files without writing them.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from random import Random
from typing import Any

from tsuyulabo_api.domain.puzzles import cleaning, meal, temperature, training

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "packages/fixtures/puzzles"
VERIFIERS = {
    "meal": meal.verify,
    "training": training.verify,
    "cleaning": cleaning.verify,
    "temperature": temperature.verify,
}
type Case = tuple[str, dict[str, Any]]


def case(
    kind: str, name: str, params: dict, submission: dict, expected: dict, description: str = ""
) -> Case:
    return name, {
        "kind": kind,
        "description": description or name.replace("_", " "),
        "params": deepcopy(params),
        "submission": submission,
        "expected": expected,
    }


def invalid(reason: str) -> dict:
    return {"valid": False, "reason": reason}


def meal_cases() -> list[Case]:
    def params(shapes: list[str]) -> dict:
        p, _ = meal.generate(Random(1), {"theme": "banana"})
        p["pieces"] = [{"shape": shape, "ingredient": "banana"} for shape in shapes]
        return p

    def submission(cells: list[tuple[int, int, int]], elapsed: int = 30000) -> dict:
        return {
            "moves": [{"p": p, "r": r, "c": c, "t": i} for i, (p, r, c) in enumerate(cells)],
            "elapsed_ms": elapsed,
        }

    def expected(score: int, lines: int = 0, combo: int = 0, themed: int = 0) -> dict:
        return {
            "valid": True,
            "score": score,
            "lines": lines,
            "max_combo": combo,
            "theme_cells": themed,
        }

    p = params(["m1"] * 18)
    cases = [
        case("meal", "empty", p, submission([]), expected(0)),
        case(
            "meal",
            "hand_order",
            p,
            submission([(2, 0, 0), (0, 0, 1), (1, 0, 2), (5, 0, 3)]),
            expected(4),
        ),
    ]
    cells = (
        [(i - 1, 0, i) for i in range(1, 8)] + [(i + 6, i, 0) for i in range(1, 8)] + [(14, 0, 0)]
    )
    cases.append(
        case(
            "meal",
            "row_column_intersection",
            p,
            submission(cells),
            expected(540, 2, 1, 15),
            "15 placed cells + 300 for two lines + 15*15 theme; intersection counted once",
        )
    )
    chain = [(0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 0, 4), (4, 1, 4), (5, 2, 4)]
    cases.append(
        case(
            "meal",
            "combo_chain",
            params(["i4h"] * 6),
            submission(chain),
            expected(834, 3, 3, 24),
            "24 cells + 100+150+200 line scores + 24*15 theme",
        )
    )
    reset = chain[:4] + [(4, 7, 0), (5, 1, 4), (6, 2, 4)]
    cases.append(
        case(
            "meal",
            "combo_reset",
            params(["i4h"] * 4 + ["m1", "i4h", "i4h"]),
            submission(reset),
            expected(735, 3, 2, 24),
        )
    )
    mixed = params(["i4h"] * 3)
    mixed["pieces"][1]["ingredient"] = "apple"
    cases.append(
        case(
            "meal", "mixed_theme", mixed, submission([(0, 0, 0), (1, 0, 4)]), expected(168, 1, 1, 4)
        )
    )
    edge = {"moves": [{"p": 0, "r": 7, "c": 7, "t": 31500}], "elapsed_ms": 31500}
    cases.append(case("meal", "inclusive_time_grace", p, edge, expected(1)))
    for name, cells, reason in [
        ("future_hand", [(3, 0, 0)], "not_in_hand"),
        ("reused_piece", [(0, 0, 0), (0, 0, 1)], "already_placed"),
        ("outside_board", [(0, 8, 0)], "out_of_bounds"),
        ("occupied_cell", [(0, 0, 0), (1, 0, 0)], "cell_occupied"),
    ]:
        cases.append(case("meal", name, p, submission(cells), invalid(reason)))
    cases.append(
        case(
            "meal",
            "late_move",
            p,
            {"moves": [{"p": 0, "r": 0, "c": 0, "t": 31501}], "elapsed_ms": 31501},
            invalid("time_exceeded"),
        )
    )
    cases.append(
        case(
            "meal",
            "time_backwards",
            p,
            {
                "moves": [{"p": 0, "r": 0, "c": 0, "t": 2}, {"p": 1, "r": 0, "c": 1, "t": 1}],
                "elapsed_ms": 2,
            },
            invalid("non_monotonic_time"),
        )
    )
    return cases


def training_cases() -> list[Case]:
    cases = []
    for day, elapsed, stars in [
        (2, 11999, 3),
        (2, 12000, 2),
        (2, 24999, 2),
        (2, 25000, 1),
        (4, 17279, 3),
        (4, 17280, 2),
        (4, 35999, 2),
        (4, 36000, 1),
    ]:
        p, secret = training.generate(Random(102), {"research_day": day})
        cases.append(
            case(
                "training",
                f"day{day}_{elapsed}ms",
                p,
                {**secret, "elapsed_ms": elapsed},
                {"valid": True, "stars": stars},
            )
        )
    p, secret = training.generate(Random(102), {})
    path = secret["path"]
    for name, bad, reason in [
        ("short_path", path[:-1], "wrong_length"),
        ("outside_grid", path[:-1] + [25], "out_of_bounds"),
        ("repeated_cell", path[:-1] + [path[0]], "revisit"),
        ("diagonal_step", [path[1], path[0], *path[2:]], "not_adjacent"),
        ("wrong_start", path[::-1], "bad_start"),
    ]:
        cases.append(case("training", name, p, {"path": bad, "elapsed_ms": 1000}, invalid(reason)))
    # Use other generated valid Hamiltonian paths, retaining the relevant endpoints.
    alternate = None
    for seed in range(10000):
        candidate = training.hamiltonian_path(Random(seed), 5)
        if candidate[0] == path[0] and candidate[-1] != path[-1]:
            alternate = candidate
            break
    assert alternate is not None
    cases.append(
        case(
            "training", "wrong_end", p, {"path": alternate, "elapsed_ms": 1000}, invalid("bad_end")
        )
    )
    alternate = None
    for seed in range(10000):
        candidate = training.hamiltonian_path(Random(seed), 5)
        if candidate[0] == path[0] and candidate[-1] == path[-1]:
            positions = [candidate.index(cp["cell"]) for cp in p["checkpoints"]]
            if positions != sorted(positions):
                alternate = candidate
                break
    assert alternate is not None
    cases.append(
        case(
            "training",
            "checkpoint_order",
            p,
            {"path": alternate, "elapsed_ms": 1000},
            invalid("checkpoint_order"),
        )
    )
    cases.append(
        case(
            "training",
            "negative_elapsed",
            p,
            {**secret, "elapsed_ms": -1},
            invalid("non_monotonic_time"),
        )
    )
    cases.append(
        case(
            "training",
            "expired_elapsed",
            p,
            {**secret, "elapsed_ms": 600001},
            invalid("time_exceeded"),
        )
    )
    return cases


def cleaning_cases() -> list[Case]:
    p, _ = cleaning.generate(Random(1), {})
    p.update(period_ms=1000, phase=0)
    cases = []
    for name, taps, score, grades in [
        ("perfect_cap", [250, 750, 1250], 100, ["perfect"] * 3),
        ("all_good", [300, 800, 1300], 66, ["good"] * 3),
        ("all_miss", [0, 500, 1000], 15, ["miss"] * 3),
        ("mixed", [250, 800, 1000], 61, ["perfect", "good", "miss"]),
        ("inclusive_limit", [250, 750, 10000], 73, ["perfect", "perfect", "miss"]),
        ("one_perfect", [0, 500, 1250], 44, ["miss", "miss", "perfect"]),
        ("perfect_boundary", [220, 280, 780], 100, ["perfect"] * 3),
        ("good_boundary", [175, 325, 825], 66, ["good"] * 3),
        ("outside_perfect", [219, 281, 781], 66, ["good"] * 3),
        ("outside_good", [174, 326, 826], 15, ["miss"] * 3),
    ]:
        cases.append(
            case(
                "cleaning",
                name,
                p,
                {"taps": taps, "elapsed_ms": taps[-1]},
                {"valid": True, "score": score, "grades": grades},
            )
        )
    for name, taps, elapsed, reason in [
        ("too_few", [250, 750], 750, "wrong_tap_count"),
        ("too_many", [1, 2, 3, 4], 4, "wrong_tap_count"),
        ("same_time", [250, 250, 750], 750, "non_monotonic_time"),
        ("time_backwards", [750, 250, 1250], 1250, "non_monotonic_time"),
        ("late_tap", [250, 750, 10001], 10001, "time_exceeded"),
        ("negative_tap", [-1, 250, 750], 750, "non_monotonic_time"),
        ("elapsed_before_tap", [250, 750, 1250], 1249, "non_monotonic_time"),
    ]:
        cases.append(
            case("cleaning", name, p, {"taps": taps, "elapsed_ms": elapsed}, invalid(reason))
        )
    return cases


def temperature_cases() -> list[Case]:
    p, _ = temperature.generate(Random(1), {})
    p["phase"] = 0
    cases = []
    for name, stop, score, grade in [
        ("zero_crossing", 0, 100, "perfect"),
        ("hot_peak", 400, 0, "miss"),
        ("cold_peak", 1200, 0, "miss"),
        ("perfect", 10, 95, "perfect"),
        ("good", 50, 73, "good"),
        ("miss", 100, 46, "miss"),
        ("long_play", 10000, 0, "miss"),
    ]:
        cases.append(
            case(
                "temperature",
                name,
                p,
                {"stop_ms": stop, "elapsed_ms": stop},
                {"valid": True, "score": score, "grade": grade},
            )
        )
    half = {**p, "amp_c": 0, "center_c": 25.375}
    cases.append(
        case(
            "temperature",
            "half_rounds_up",
            half,
            {"stop_ms": 0, "elapsed_ms": 0},
            {"valid": True, "score": 93, "grade": "perfect"},
        )
    )
    for name, stop, elapsed, reason in [
        ("negative_stop", -1, 0, "non_monotonic_time"),
        ("negative_elapsed", 0, -1, "non_monotonic_time"),
        ("elapsed_before_stop", 100, 99, "non_monotonic_time"),
        ("expired_stop", 600001, 600001, "time_exceeded"),
        ("expired_elapsed", 100, 600001, "time_exceeded"),
        ("fractional_timestamp", 1.5, 2, "non_monotonic_time"),
    ]:
        cases.append(
            case("temperature", name, p, {"stop_ms": stop, "elapsed_ms": elapsed}, invalid(reason))
        )
    return cases


def build() -> list[Case]:
    return meal_cases() + training_cases() + cleaning_cases() + temperature_cases()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    cases = build()
    for name, fixture in cases:
        result = VERIFIERS[fixture["kind"]](fixture["params"], fixture["submission"]).to_dict()
        assert result == fixture["expected"], (fixture["kind"], name, result, fixture["expected"])
        path = FIXTURES / fixture["kind"] / f"{name}.json"
        rendered = json.dumps(fixture, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            assert path.read_text(encoding="utf-8") == rendered, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
    print(f"{'Checked' if args.check else 'Generated'} {len(cases)} puzzle fixtures")


if __name__ == "__main__":
    main()
