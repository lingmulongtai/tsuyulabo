from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Friendship
from tsuyulabo_api.routers import sumo

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_house_limit_replay_and_ownership(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with (
        GameClient(sessions, sumo.router) as player,
        GameClient(sessions, sumo.router) as stranger,
    ):
        player.app.state.brain_adapter = BrainAdapter()
        adult = await make_adult(sessions, player, sex="m")
        choices = (await player.get("/v1/sumo/challenges")).json()
        assert choices["males"][0]["id"] == adult
        assert choices["opponents"][0]["id"] == "house"
        body = {"adult_id": adult, "opponent_id": "house"}
        first = await player.post("/v1/sumo/bouts", body)
        assert first.status_code == 200, first.text
        replay = first.json()
        assert replay["replay"]["frames"]
        assert (await stranger.get(f"/v1/sumo/bouts/{replay['id']}")).status_code == 404
        assert len((await player.get("/v1/sumo/bouts")).json()) == 1
        for _ in range(2):
            assert (await player.post("/v1/sumo/bouts", body)).status_code == 200
        assert (await player.post("/v1/sumo/bouts", body)).status_code == 409
        assert (await player.get("/v1/sumo/challenges")).json()["remaining"] == 0


async def test_friend_opponent_requires_friendship(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with (
        GameClient(sessions, sumo.router) as player,
        GameClient(sessions, sumo.router) as friend,
    ):
        player.app.state.brain_adapter = BrainAdapter()
        friend.app.state.brain_adapter = BrainAdapter()
        mine = await make_adult(sessions, player, sex="m")
        theirs = await make_adult(sessions, friend, sex="m")
        body = {"adult_id": mine, "opponent_id": theirs}
        assert (await player.post("/v1/sumo/bouts", body)).status_code == 404
        assert (await friend.post("/v1/sumo/bouts", body)).status_code == 404
        async with sessions() as session, session.begin():
            session.add(Friendship(user_id=player.user["id"], friend_id=friend.user["id"]))
        public = (await player.get("/v1/sumo/challenges")).json()["opponents"]
        assert public[1]["id"] == theirs and public[1]["traits"] == []
        assert (await player.post("/v1/sumo/bouts", body)).status_code == 200
