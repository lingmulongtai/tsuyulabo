from __future__ import annotations

from typing import Any

from tsuyulabo_api.db.models import User
from tsuyulabo_api.routers import zukan

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_collection_tracks_unique_owned_discoveries(sessions: Any) -> None:
    async with GameClient(sessions, zukan.router) as game:
        assert (await game.get("/v1/zukan")).json()["completion"] == {"behaviors": 0, "strains": 0}
        await make_adult(sessions, game, strain="white")
        await make_adult(sessions, game, strain="white")
        async with sessions() as session, session.begin():
            user = await session.get(User, game.user["id"])
            user.observed_behaviors = ["rest"]
        completion = (await game.get("/v1/zukan")).json()["completion"]
        assert completion == {"behaviors": 1 / 9, "strains": 1 / 6}
