from __future__ import annotations

from typing import Any
from uuid import uuid4

from tsuyulabo_api.routers import sleep, team

from .adult_fixtures import make_adult
from .game_support import GameClient
from .test_team_routes import put_team


async def test_sleep_slots_limits_bonus_recovery_replay(sessions: Any) -> None:
    async with GameClient(sessions, sleep.router, team.router) as game:
        adult_id = await make_adult(sessions, game, energy=10)
        await put_team(game, [adult_id])
        assert (await game.post("/v1/sleep/start")).status_code == 409
        assert (await game.post("/v1/sleep/end")).json()["error"]["code"] == "no_active_sleep"
        await game.advance(hours=14)
        assert (await game.post("/v1/sleep/start")).status_code == 200
        assert (await game.post("/v1/sleep/start")).json()["error"]["code"] == "daily_limit_reached"
        assert (await game.post("/v1/sleep/end")).status_code == 409
        await game.advance(to="next_day")
        key = str(uuid4())
        response = await game.post("/v1/sleep/end", key=key)
        assert response.status_code == 200, response.text
        assert response.json()["hours"] == 10 and response.json()["bonus"] == 200
        assert response.json()["energy_recovered"][adult_id] == 100
        assert (await game.post("/v1/sleep/end", key=key)).json() == response.json()
        assert (await game.post("/v1/sleep/end")).json()["error"]["code"] == "daily_limit_reached"
        assert (await game.get("/v1/me")).json()["balances"]["shizuku"] == 500
