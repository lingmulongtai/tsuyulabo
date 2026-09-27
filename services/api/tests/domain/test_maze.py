from __future__ import annotations

from datetime import datetime

from tsuyulabo_api.domain import maze
from tsuyulabo_api.domain.clock import JST


def test_week_boundary_and_shared_connected_maze() -> None:
    week, deadline = maze.week_at(datetime(2027, 1, 3, 23, 59, tzinfo=JST))
    assert week == "2026-W53"
    assert maze.week_at(deadline)[0] == "2027-W01"
    for index in range(1, 53):
        grid = maze.generate(f"2026-W{index:02d}")
        assert grid == maze.generate(f"2026-W{index:02d}")
        field = maze.distances(grid, (1, 1))
        assert (7, 7) in field
        assert len(field) == sum(row.count(".") for row in grid["grid"])


def test_replay_determinism_and_path_distance_fields() -> None:
    grid = maze.generate("2026-W39")
    observations = []

    def policy(observation: dict) -> dict:
        observations.append(observation)
        return {"forward": 0.5, "left": 0.2, "right": 0.2, "stay": 0.1}

    tokens = [{"x": 7, "y": 7, "cue": "banana"}]
    first = maze.run(grid, tokens, 42, policy)
    assert first == maze.run(grid, tokens, 42, policy)
    assert first != maze.run(grid, tokens, 43, policy)
    assert len(first["frames"]) == first["steps"] + 1 <= 401
    assert all(maze.is_open(grid, f["x"], f["y"]) for f in first["frames"])
    assert observations[0]["current"]["cues"]["banana"] < 1
