from __future__ import annotations

from random import Random
from typing import Any
from uuid import uuid4

import pytest
from tsuyulabo_api.domain.names import NAME_POOL
from tsuyulabo_api.routers import adults, weeks

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_eclosion_names_are_seeded_unique_and_preserve_existing(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(weeks, "rng", lambda: Random(42))
    results = []
    for _ in range(2):
        async with GameClient(sessions, weeks.router, adults.router) as game:
            legacy = await make_adult(sessions, game, name="ショウジョウバエ")
            names = []
            for _ in range(2):
                await game.post("/v1/weeks")
                await game.advance(to="eclosion")
                key = str(uuid4())
                response = await game.post("/v1/weeks/current/eclose", key=key)
                assert response.status_code == 200, response.text
                assert (
                    await game.post("/v1/weeks/current/eclose", key=key)
                ).json() == response.json()
                names.append(response.json()["adult"]["name"])
            assert len(set(names)) == 2
            assert all(name in NAME_POOL for name in names)
            assert (await game.get(f"/v1/adults/{legacy}")).json()["name"] == "ショウジョウバエ"
            results.append(names)
    assert results[0] == results[1]
