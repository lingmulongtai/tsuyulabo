from __future__ import annotations

from typing import Any

from tsuyulabo_api.routers import adults

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_adult_details_level_cost_unlock_and_errors(sessions: Any) -> None:
    async with GameClient(sessions, adults.router) as game:
        adult_id = await make_adult(sessions, game, level=9)
        assert len((await game.get("/v1/adults")).json()) == 1
        detail = (await game.get(f"/v1/adults/{adult_id}")).json()
        assert len(detail["preferences"]) == 5
        response = await game.post(f"/v1/adults/{adult_id}/level-up")
        assert response.status_code == 200, response.text
        assert response.json()["level"] == 10 and response.json()["cost"] == 180
        assert len(response.json()["subskills"]) == 1
        assert (await game.get("/v1/me")).json()["balances"]["shizuku"] == 120
        insufficient = await game.post(f"/v1/adults/{adult_id}/level-up")
        assert insufficient.json()["error"]["code"] == "insufficient_funds"
        capped = await make_adult(sessions, game, stars=1, level=20)
        assert (await game.post(f"/v1/adults/{capped}/level-up")).json()["error"][
            "code"
        ] == "level_cap_reached"
        assert (await game.get("/v1/adults/missing")).status_code == 404
        async with GameClient(sessions, adults.router) as other:
            assert (await other.get(f"/v1/adults/{adult_id}")).status_code == 404
            assert (await other.post(f"/v1/adults/{adult_id}/level-up")).status_code == 404
