from __future__ import annotations

from typing import Any

import pytest
from tsuyulabo_api.db.models import Puzzle
from tsuyulabo_api.routers import puzzles, weeks

from .game_support import GameClient


@pytest.mark.parametrize("seconds,stars", [(11.999, 3), (12, 2), (25, 1), (599, 1)])
async def test_training_stars_cannot_be_forged_with_short_elapsed_time(
    sessions: Any, seconds: float, stars: int
) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        await game.post("/v1/weeks")
        await game.advance(to="next_day")
        issued = (
            await game.post(
                "/v1/puzzles", {"kind": "training", "cue": "banana", "valence": "reward"}
            )
        ).json()
        async with sessions() as session:
            puzzle = await session.get(Puzzle, issued["puzzle_id"])
            solution = puzzle.secret["path"]
        game.clock.advance(seconds)
        response = await game.post(
            f"/v1/puzzles/{puzzle.id}/submit", {"path": solution, "elapsed_ms": 0}
        )
        assert response.status_code == 200
        assert response.json()["stars"] == stars
