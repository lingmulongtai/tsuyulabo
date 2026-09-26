from __future__ import annotations

from copy import deepcopy
from random import Random

import pytest
from tsuyulabo_api.domain.puzzles import training


@pytest.mark.parametrize("day,n,count", [(2, 5, 5), (3, 5, 5), (4, 6, 7), (7, 6, 7)])
def test_generation(day: int, n: int, count: int) -> None:
    paths = set()
    for seed in range(100):
        params, secret = training.generate(Random(seed), {"research_day": day})
        assert params["n"] == n and len(params["checkpoints"]) == count
        assert "path" not in params and "seed" not in params
        path = secret["path"]
        paths.add(tuple(path))
        assert training.verify(params, {"path": path, "elapsed_ms": 5000}).stars == 3
        for k, checkpoint in enumerate(params["checkpoints"]):
            assert abs(path.index(checkpoint["cell"]) - round(k * (n * n - 1) / (count - 1))) <= 1
    assert len(paths) > 50


@pytest.mark.parametrize(
    "day,times", [(2, (11999, 12000, 24999, 25000)), (4, (17279, 17280, 35999, 36000))]
)
def test_star_boundaries(day: int, times: tuple[int, ...]) -> None:
    params, secret = training.generate(Random(1), {"research_day": day})
    assert [training.verify(params, {**secret, "elapsed_ms": t}).stars for t in times] == [
        3,
        2,
        2,
        1,
    ]


def test_invalid_paths() -> None:
    params, secret = training.generate(Random(1), {})
    path = secret["path"]
    for bad, reason in [
        (path[:-1], "wrong_length"),
        (path[:-1] + [-1], "out_of_bounds"),
        (path[:-1] + [path[0]], "revisit"),
        ([path[1], path[0], *path[2:]], "not_adjacent"),
        (path[::-1], "bad_start"),
    ]:
        assert training.verify(params, {"path": bad, "elapsed_ms": 1000}).reason == reason
    p = deepcopy(params)
    p["checkpoints"][-1]["cell"] = path[-2]
    assert training.verify(p, {**secret, "elapsed_ms": 1000}).reason == "bad_end"
    p = deepcopy(params)
    p["checkpoints"][1]["cell"], p["checkpoints"][2]["cell"] = (
        p["checkpoints"][2]["cell"],
        p["checkpoints"][1]["cell"],
    )
    assert training.verify(p, {**secret, "elapsed_ms": 1000}).reason == "checkpoint_order"
    assert training.roll(Random(1), 3) == {"hirameki": True, "learning_strength": 0.72}
    assert training.skill_unlocked("banana", 0.6) is None
    assert training.skill_unlocked("banana", 0.601) == "banana_search"
    assert training.skill_unlocked("banana", -0.601) == "banana_avoid"
