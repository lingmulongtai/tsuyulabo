from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Friendship, Job, MazeSlot, User
from tsuyulabo_api.routers import races
from tsuyulabo_api.services.jobs import InlineJobQueue
from tsuyulabo_api.services.maze_race import handler

from .adult_fixtures import make_adult
from .game_support import GameClient


async def prepare(sessions: async_sessionmaker[AsyncSession], game: GameClient) -> str:
    game.app.state.brain_adapter = BrainAdapter()
    game.app.state.job_queue = InlineJobQueue(sessions, {"brain.maze_run": handler()})
    return await make_adult(sessions, game)


async def test_inline_deterministic_replacement_and_idempotency(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with GameClient(sessions, races.router) as game:
        adult = await prepare(sessions, game)
        current = (await game.get("/v1/races/current")).json()
        body = {"week": current["week"], "adult_id": adult, "placements": []}
        key = str(uuid4())
        first = await game.post("/v1/races/current/entry", body, key)
        assert first.status_code == 200, first.text
        assert (await game.post("/v1/races/current/entry", body, key)).json() == first.json()
        replay = (await game.get(f"/v1/races/entries/{first.json()['id']}/replay")).json()
        assert replay["entry"]["status"] == "succeeded"
        assert replay["result"]["steps"] <= 400
        second = (await game.post("/v1/races/current/entry", body)).json()
        assert second["id"] != first.json()["id"]
        replay2 = (await game.get(f"/v1/races/entries/{second['id']}/replay")).json()
        assert replay2["result"] == replay["result"]
        ranking = (await game.get("/v1/races/current/ranking")).json()["entries"]
        assert len(ranking) == 1 and ranking[0]["entry_id"] == second["id"]
        async with sessions() as session:
            slot = await session.get(MazeSlot, (game.user["id"], current["week"]))
            assert slot.entry_id == second["id"]


async def test_ownership_friend_visibility_and_validation(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with (
        GameClient(sessions, races.router) as owner,
        GameClient(sessions, races.router) as other,
    ):
        adult = await prepare(sessions, owner)
        current = (await owner.get("/v1/races/current")).json()
        body = {"week": current["week"], "adult_id": adult, "placements": []}
        assert (await other.post("/v1/races/current/entry", body)).status_code == 404
        for tokens in (
            [{"x": 0, "y": 0, "cue": "banana"}],
            [{"x": 1, "y": 1, "cue": "banana"}] * 2,
            [{"x": 1, "y": 1, "cue": "banana"}] * 4,
            [{"x": 1, "y": 1, "cue": "unknown"}],
            [{"x": True, "y": 1, "cue": "banana"}],
        ):
            assert (
                await owner.post("/v1/races/current/entry", body | {"placements": tokens})
            ).status_code == 422
        entry = (await owner.post("/v1/races/current/entry", body)).json()
        path = f"/v1/races/entries/{entry['id']}/replay"
        assert (await other.get(path)).status_code == 404
        assert (await other.get("/v1/races/current/ranking")).json()["entries"] == []
        async with sessions() as session, session.begin():
            session.add(Friendship(user_id=other.user["id"], friend_id=owner.user["id"]))
            user = await session.get(User, owner.user["id"])
            user.dev_time_offset_s = 30 * 86400
        assert (await owner.get("/v1/races/current")).json()["week"] == current["week"]
        assert (await other.get(path)).status_code == 200
        assert len((await other.get("/v1/races/current/ranking")).json()["entries"]) == 1
        owner.clock.advance(7 * 86400)
        assert (await owner.post("/v1/races/current/entry", body)).status_code == 409
        assert (await owner.get("/v1/races/current")).json()["my_entry"] is None


async def test_enqueue_failure_is_visible(sessions: async_sessionmaker[AsyncSession]) -> None:
    class BrokenQueue:
        async def enqueue(self, *args: Any) -> None:
            raise RuntimeError("offline")

    async with GameClient(sessions, races.router) as game:
        adult = await prepare(sessions, game)
        game.app.state.job_queue = BrokenQueue()
        current = (await game.get("/v1/races/current")).json()
        entry = (
            await game.post(
                "/v1/races/current/entry",
                {
                    "week": current["week"],
                    "adult_id": adult,
                    "placements": [],
                },
            )
        ).json()
        async with sessions() as session:
            assert (await session.get(Job, entry["job_id"])).status == "failed"
        assert (await game.get("/v1/races/current")).json()["my_entry"]["status"] == "failed"
