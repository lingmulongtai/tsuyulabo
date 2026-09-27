from __future__ import annotations

from typing import Any

from tsuyulabo_api.routers import weeks

from .game_support import GameClient


async def test_negative_presentation_ecloses_without_debiting_empty_research_wallet(
    sessions: Any,
) -> None:
    async with GameClient(sessions, weeks.router) as game:
        await game.post("/v1/weeks")
        await game.advance(to="eclosion")
        presentation = (await game.get("/v1/weeks/current/presentation")).json()
        assert presentation["points"] < 0
        assert presentation["shizuku"] == presentation["research_points"] == 0
        before = (await game.get("/v1/me")).json()
        response = await game.post("/v1/weeks/current/eclose")
        assert response.status_code == 200, response.text
        after = (await game.get("/v1/me")).json()
        assert after["balances"] == before["balances"]
        assert after["research_rank"] == before["research_rank"] == 1
