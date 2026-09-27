from __future__ import annotations

from typing import Any

import pytest
from tsuyulabo_api.db.models import User
from tsuyulabo_api.routers import friends, weeks
from tsuyulabo_api.services.ledger import add_material

from .game_support import GameClient


@pytest.mark.parametrize("state", ["active_week", "eclosed_week", "like", "gift"])
async def test_reset_rejects_rewinding_existing_game_state(sessions: Any, state: str) -> None:
    async with (
        GameClient(sessions, weeks.router, friends.router) as game,
        GameClient(sessions, friends.router) as friend,
    ):
        await game.advance(to="next_day")
        if state.endswith("week"):
            assert (await game.post("/v1/weeks")).status_code == 201
            if state == "eclosed_week":
                await game.advance(to="eclosion")
                assert (await game.post("/v1/weeks/current/eclose")).status_code == 200
        else:
            await game.post("/v1/friends", {"friend_code": friend.user["friend_code"]})
            if state == "gift":
                async with sessions() as session, session.begin():
                    await add_material(session, game.user["id"], "banana", 1)
            path = f"/v1/friends/{friend.user['id']}/{state}"
            body = {"material": "banana", "amount": 1} if state == "gift" else None
            assert (await game.post(path, body)).status_code == 200
        before = (await game.get("/v1/dev/time")).json()["dev_time_offset_s"]
        response = await game.post("/v1/dev/time/reset")
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "time_reversed"
        assert (await game.get("/v1/dev/time")).json()["dev_time_offset_s"] == before


async def test_advance_cannot_overflow_database_integer(sessions: Any) -> None:
    async with GameClient(sessions) as game:
        response = await game.post("/v1/dev/time/advance", {"hours": 600_000})
        assert response.status_code == 422
        async with sessions() as session:
            assert (await session.get(User, game.user["id"])).dev_time_offset_s == 0


async def test_zero_offset_reset_remains_safe_after_start(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router) as game:
        await game.post("/v1/weeks")
        assert (await game.post("/v1/dev/time/reset")).status_code == 200
