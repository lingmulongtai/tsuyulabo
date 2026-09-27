from __future__ import annotations

from typing import Any

import pytest
from tsuyulabo_api.db.models import Adult, LarvaState
from tsuyulabo_api.routers import adults, home, puzzles, team, weeks
from tsuyulabo_api.services.brain_state import snapshot

from .game_support import GameClient
from .puzzle_solvers import play
from .test_team_routes import put_team


async def test_training_and_eclosion_persist_bytes_and_read_cached_preferences(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with GameClient(
        sessions, weeks.router, puzzles.router, adults.router, team.router, home.router
    ) as game:
        week_id = (await game.post("/v1/weeks")).json()["id"]
        await game.advance(to="next_day")
        await play(game, sessions, "training")
        async with sessions() as session:
            larva = await session.get(LarvaState, week_id)
            assert larva.learned_weights and "state" not in larva.brain_snapshot
            assert larva.preferences["banana"] > 0
            assert len(larva.brain_snapshot["training"]) == 1
            assert game.app.state.brain_adapter.restore(snapshot(larva)).values["banana"] > 0
        await game.advance(to="eclosion")
        eclosed = await game.post("/v1/weeks/current/eclose")
        assert eclosed.status_code == 200, eclosed.text
        adult_id = eclosed.json()["adult"]["id"]
        async with sessions() as session:
            adult = await session.get(Adult, adult_id)
            assert adult.learned_weights and adult.brain_params
            assert adult.preferences["banana"] > 0
        await put_team(game, [adult_id])

        def no_simulation(*args: object, **kwargs: object) -> None:
            pytest.fail("read routes must use row caches")

        monkeypatch.setattr(game.app.state.brain_adapter, "preferences", no_simulation)
        monkeypatch.setattr(game.app.state.brain_adapter, "restore", no_simulation)
        for _ in range(2):
            assert (await game.get("/v1/home")).status_code == 200
            assert (await game.get("/v1/adults")).status_code == 200
