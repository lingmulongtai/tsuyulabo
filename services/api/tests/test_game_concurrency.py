from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select
from tsuyulabo_api.db.models import CareEvent, Week
from tsuyulabo_api.routers import puzzles, weeks

from .game_support import GameClient


async def test_concurrent_week_starts_and_distinct_puzzle_submissions(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        started = await asyncio.gather(game.post("/v1/weeks"), game.post("/v1/weeks"))
        assert sorted(r.status_code for r in started) == [201, 409]
        issued = await asyncio.gather(
            game.post("/v1/puzzles", {"kind": "meal"}),
            game.post("/v1/puzzles", {"kind": "meal"}),
        )
        submissions = await asyncio.gather(
            *(
                game.post(
                    f"/v1/puzzles/{p.json()['puzzle_id']}/submit", {"moves": [], "elapsed_ms": 0}
                )
                for p in issued
            )
        )
        assert sorted(r.status_code for r in submissions) == [200, 409]
        async with sessions() as session:
            assert len((await session.scalars(select(Week))).all()) == 1
            assert len((await session.scalars(select(CareEvent))).all()) == 1
