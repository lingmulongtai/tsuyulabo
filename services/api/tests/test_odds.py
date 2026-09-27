from __future__ import annotations

from typing import Any

from tsuyulabo_api.routers import odds

from .game_support import GameClient


async def test_public_odds_match_adjustments(sessions: Any) -> None:
    async with GameClient(sessions, odds.router) as game:
        response = await game.client.get("/v1/odds")
        assert response.status_code == 200
        data = response.json()
        assert data["eclosion"]["normal"] == [72, 22, 5.5, 0.5]
        assert data["adjusted"]["normal"]["both"] == [67, 25, 7.5, 0.5]
        assert data["hirameki"]["three_stars"] == 0.15
