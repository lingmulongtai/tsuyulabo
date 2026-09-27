from __future__ import annotations

from typing import Any

from tsuyulabo_api.domain.genetics import wild_type
from tsuyulabo_api.routers import adults, zukan

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_genotypes_are_revealed_but_carriers_do_not_unlock_strains(sessions: Any) -> None:
    async with GameClient(sessions, adults.router, zukan.router) as game:
        carrier = wild_type("f") | {"w": ["w", "+"], "e": ["e", "+"]}
        adult_id = await make_adult(sessions, game, genotype=carrier)
        detail = (await game.get(f"/v1/adults/{adult_id}")).json()
        listing = (await game.get("/v1/adults")).json()
        assert detail["genotype"] == carrier == listing[0]["genotype"]
        assert detail["phenotypes"] == ["wild"] and detail["mutation"] is None
        combined = wild_type("m") | {"w": ["w"], "e": ["e", "e"]}
        await make_adult(sessions, game, sex="m", strain="white", genotype=combined)
        observed = {
            row["id"] for row in (await game.get("/v1/zukan")).json()["strains"] if row["observed"]
        }
        assert observed == {"wild", "white", "ebony"}
