from __future__ import annotations

import asyncio
from typing import Any

import pytest
from tsuyulabo_api.routers import adults, brain, home, jobs, puzzles, weeks
from tsuyulabo_api.services import deferred
from tsuyulabo_api.services.training import handler

from .game_support import GameClient
from .test_queued_training import issue_training


@pytest.mark.parametrize("eclosed", [False, True])
async def test_odour_waits_for_queued_learning_across_routes(
    sessions: Any, monkeypatch: pytest.MonkeyPatch, eclosed: bool
) -> None:
    calls: list[dict[str, Any]] = []

    class Queue:
        async def enqueue(self, job_id: str, kind: str, params: dict[str, Any]) -> None:
            calls.append(params)

    monkeypatch.setattr(deferred, "LEARNING_WAIT_SECONDS", 0.01)
    async with GameClient(
        sessions,
        weeks.router,
        puzzles.router,
        jobs.router,
        home.router,
        brain.router,
        adults.router,
    ) as game:
        game.app.state.settings.brain_mode = "queue"
        game.app.state.job_queue = Queue()
        week = (await game.post("/v1/weeks")).json()
        await game.advance(to="next_day")
        path, body = await issue_training(game, sessions)
        assert (await game.post(path, body)).json()["learning_status"] == "pending"
        assert (await game.get("/v1/home")).json()["vial"]["learning_pending"]
        fly_id = week["id"]
        habitat_path = "/v1/home"
        if eclosed:
            await game.advance(to="eclosion")
            result = await game.post("/v1/weeks/current/eclose")
            assert result.status_code == 200, result.text
            fly_id = result.json()["adult"]["id"]
            habitat_path = f"/v1/adults/{fly_id}"
            assert (await game.get(habitat_path)).json()["vial"]["learning_pending"]
        observation = f"/v1/flies/{fly_id}/experiments"
        rejected = await game.post(observation, {"cue": "banana", "trials": 1})
        assert rejected.status_code == 409
        assert rejected.json()["error"]["code"] == "learning_pending"
        assert len(calls) == 1  # No observation can enqueue a stale brain snapshot.
        await handler(sessions, game.app.state.brain_adapter)(calls[0])
        assert not (await game.get(habitat_path)).json()["vial"]["learning_pending"]
        assert (await game.post(observation, {"cue": "banana", "trials": 1})).status_code == 202
        assert len(calls) == 2
        assert calls[1]["snapshot"]["training"]
        await asyncio.gather(*game.app.state.pending_calculations)
