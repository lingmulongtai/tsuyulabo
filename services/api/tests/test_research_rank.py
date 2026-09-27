from __future__ import annotations

from typing import Any

from tsuyulabo_api.services.ledger import get_account, transfer

from .game_support import GameClient


async def test_rank_counts_lifetime_earnings_and_caps_at_99(sessions: Any) -> None:
    async with GameClient(sessions) as game:
        assert game.user["research_rank"] == 1
        for earned, spent, expected in [(99, 0, 1), (1, 100, 2), (200, 0, 4), (20000, 0, 99)]:
            async with sessions() as session, session.begin():
                source = await get_account(session, "system:rewards", "research_points")
                wallet = await get_account(session, f"user:{game.user['id']}", "research_points")
                await transfer(session, source, wallet, earned, "presentation")
                if spent:
                    await transfer(session, wallet, source, spent, "purchase")
            assert (await game.get("/v1/me")).json()["research_rank"] == expected
