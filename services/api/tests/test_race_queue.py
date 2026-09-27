from __future__ import annotations

import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, Job
from tsuyulabo_api.domain.maze import run
from tsuyulabo_api.routers import races
from tsuyulabo_api.services.maze_race import simulate

from .adult_fixtures import make_adult
from .game_support import GameClient


class DeferredQueue:
    async def enqueue(self, *args: Any) -> None:
        pass


async def test_late_old_job_cannot_replace_current_entry_and_inputs_are_frozen(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with GameClient(sessions, races.router) as game:
        game.app.state.brain_adapter = BrainAdapter()
        game.app.state.job_queue = DeferredQueue()
        adult_id = await make_adult(sessions, game)
        race = (await game.get("/v1/races/current")).json()
        body = {"week": race["week"], "adult_id": adult_id, "placements": []}
        old = (await game.post("/v1/races/current/entry", body)).json()
        new = (await game.post("/v1/races/current/entry", body)).json()
        async with sessions() as session, session.begin():
            adult = await session.get(Adult, adult_id)
            adult.level = 99
            adult.preferences = {"banana": 1}
            adult.learned_weights = b"changed after submission"
            # Finish the replacement first, then deliver the superseded job.
            for entry in (new, old):
                job = await session.get(Job, entry["job_id"])
                job.result = simulate(job.params)
                job.status = "succeeded"
        current = (await game.get("/v1/races/current")).json()
        assert current["my_entry"]["id"] == new["id"]
        ranks = (await game.get("/v1/races/current/ranking")).json()["entries"]
        assert [entry["entry_id"] for entry in ranks] == [new["id"]]
        async with sessions() as session:
            jobs = (await session.scalars(select(Job))).all()
            assert len(jobs) == 2
            assert jobs[0].result == jobs[1].result


def test_path_distance_prevents_scent_crossing_walls() -> None:
    maze = {
        "grid": [
            "#########",
            "#.#.....#",
            "#.#.###.#",
            "#...#...#",
            "#####.#.#",
            "#.....#.#",
            "#.#####.#",
            "#.......#",
            "#########",
        ],
        "start": [1, 1],
        "goal": [7, 7],
    }
    observations = []

    def stationary(observation: dict) -> dict:
        observations.append(observation)
        return {"stay": 1.0}

    run(maze, [{"x": 3, "y": 1, "cue": "banana"}], 0, stationary)
    # The cue is two cells away geometrically, but six steps around the wall.
    assert observations[0]["current"]["cues"]["banana"] == math.exp(-6 / 3)
    assert not observations[0]["forward"]["open"]
