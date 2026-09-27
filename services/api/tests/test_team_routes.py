from __future__ import annotations

from typing import Any
from uuid import uuid4

from tsuyulabo_api.routers import inventory, team

from .adult_fixtures import make_adult
from .game_support import GameClient


async def put_team(game: GameClient, ids: list[str]) -> Any:
    return await game.client.put(
        "/v1/team",
        json={"adult_ids": ids},
        headers=game.headers | {"Idempotency-Key": str(uuid4())},
    )


async def test_gather_collect_reorder_and_park(sessions: Any) -> None:
    async with GameClient(sessions, team.router, inventory.router) as game:
        adult_id = await make_adult(sessions, game)
        assert (await put_team(game, [adult_id])).status_code == 200
        await game.advance(hours=8)
        gathered = (await game.get("/v1/team")).json()
        assert gathered["bag_total"] == 12
        assert (await game.get("/v1/team")).json() == gathered
        assert (await put_team(game, [adult_id])).json() == gathered
        await put_team(game, [])
        await game.advance(hours=8)
        assert (await put_team(game, [adult_id])).json() == gathered
        key = str(uuid4())
        collected = await game.post("/v1/team/collect", key=key)
        assert (await game.post("/v1/team/collect", key=key)).json() == collected.json()
        assert sum(collected.json()["materials"].values()) == 12
        assert collected.json()["shizuku"] == 17
        assert collected.json()["team"]["members"][0]["level"] == 2
        assert sum((await game.get("/v1/inventory")).json().values()) == 12
        assert (await game.post("/v1/team/collect")).json()["materials"] == {}


async def test_team_validation_and_ownership(sessions: Any) -> None:
    async with GameClient(sessions, team.router) as game:
        adult = await make_adult(sessions, game)
        assert (await put_team(game, [adult] * 6)).json()["error"]["code"] == "team_full"
        assert (await put_team(game, [adult] * 2)).status_code == 422
        assert (await put_team(game, ["missing"])).status_code == 404
        async with GameClient(sessions, team.router) as other:
            assert (await put_team(other, [adult])).status_code == 404
