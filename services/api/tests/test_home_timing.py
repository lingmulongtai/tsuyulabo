from __future__ import annotations

from time import perf_counter
from typing import Any

import pytest
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.routers import adults, home, puzzles, team, weeks

from .game_support import GameClient
from .puzzle_solvers import play
from .test_team_routes import put_team


@pytest.mark.eval
async def test_trained_week_home_and_adults_are_bounded(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with GameClient(
        sessions, weeks.router, puzzles.router, adults.router, home.router, team.router
    ) as game:
        brain = game.app.state.brain_adapter = BrainAdapter()
        await game.post("/v1/weeks")
        await game.advance(to="next_day")
        for _ in range(3):
            await play(game, sessions, "training")

        async def check_home() -> None:
            for _ in range(3):
                start = perf_counter()
                response = await game.get("/v1/home")
                duration = perf_counter() - start
                assert response.status_code == 200
                assert duration < 0.3, f"home took {duration * 1000:.1f} ms"

        await check_home()
        await game.advance(to="eclosion")
        response = await game.post("/v1/weeks/current/eclose")
        assert response.status_code == 200, response.text
        await put_team(game, [response.json()["adult"]["id"]])

        def no_simulations(*args: object, **kwargs: object) -> None:
            pytest.fail("cached read attempted brain work")

        monkeypatch.setattr(brain, "restore", no_simulations)
        monkeypatch.setattr(brain, "preferences", no_simulations)
        await check_home()
        assert (await game.get("/v1/adults")).status_code == 200
