from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult, Job, LarvaState, Puzzle, Week
from tsuyulabo_api.routers import jobs, puzzles, weeks
from tsuyulabo_api.services import deferred
from tsuyulabo_api.services.jobs import InlineJobQueue
from tsuyulabo_api.services.training import handler

from .game_support import GameClient


async def issue_training(game: GameClient, sessions: Any) -> tuple[str, dict]:
    issued = (
        await game.post("/v1/puzzles", {"kind": "training", "cue": "banana", "valence": "reward"})
    ).json()
    async with sessions() as session:
        puzzle = await session.get(Puzzle, issued["puzzle_id"])
        body = {"path": puzzle.secret["path"], "elapsed_ms": 5000}
    game.clock.advance(5)
    return f"/v1/puzzles/{puzzle.id}/submit", body


async def test_queue_waits_for_learning_and_concurrent_replays_match(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router, jobs.router) as game:
        game.app.state.settings.brain_mode = "queue"
        game.app.state.job_queue = InlineJobQueue(
            sessions, {"brain.training": handler(sessions, game.app.state.brain_adapter)}
        )
        week = (await game.post("/v1/weeks")).json()
        await game.advance(to="next_day")
        path, body = await issue_training(game, sessions)
        key = str(uuid4())
        first, replay = await asyncio.gather(game.post(path, body, key), game.post(path, body, key))
        assert first.status_code == 200, first.text
        assert first.json() == replay.json()
        assert first.json()["learning_status"] == "completed"
        assert first.json()["association"]["value"] > 0
        async with sessions() as session:
            assert len((await session.scalars(select(Job))).all()) == 1
            assert len((await session.get(LarvaState, week["id"])).brain_snapshot["training"]) == 1


async def test_timeout_replay_is_fixed_and_late_learning_updates_adult(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    class Queue:
        async def enqueue(self, job_id: str, kind: str, params: dict) -> None:
            calls.append((job_id, kind, params))

    monkeypatch.setattr(deferred, "LEARNING_WAIT_SECONDS", 0.01)
    async with GameClient(sessions, weeks.router, puzzles.router, jobs.router) as game:
        game.app.state.settings.brain_mode = "queue"
        game.app.state.job_queue = Queue()
        week = (await game.post("/v1/weeks")).json()
        await game.advance(to="next_day")
        path, body = await issue_training(game, sessions)
        key = str(uuid4())
        pending = await game.post(path, body, key)
        assert pending.json()["learning_status"] == "pending"
        assert pending.json()["association"] is None
        assert len(calls) == 1
        async with sessions() as session, session.begin():
            larva = await session.get(LarvaState, week["id"])
            snapshot, params = game.app.state.brain_adapter.eclose(
                larva.brain_snapshot, ["brave", "glutton"], "f", 1
            )
            adult = Adult(
                user_id=game.user["id"],
                week_id=week["id"],
                name="test",
                sex="f",
                strain="wild",
                stars=3,
                brain_snapshot=snapshot,
                brain_params=params,
                preferences={"banana": 0},
            )
            session.add(adult)
            await session.flush()
            stored = await session.get(Week, week["id"])
            stored.adult_id, stored.status = adult.id, "eclosed"
            adult_id = adult.id
        run = handler(sessions, game.app.state.brain_adapter)
        completed = await run(calls[0][2])
        assert completed["learning_status"] == "completed"
        assert (await game.post(path, body, key)).json() == pending.json()
        assert await run(calls[0][2]) == completed  # Queue redelivery does not train twice.
        async with sessions() as session:
            adult = await session.get(Adult, adult_id)
            assert adult.preferences["banana"] > 0
            assert len(adult.brain_snapshot["training"]) == 1
        await asyncio.gather(*game.app.state.pending_calculations)
