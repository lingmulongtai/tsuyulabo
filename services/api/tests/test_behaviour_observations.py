from __future__ import annotations

from sqlalchemy import select
from tsuyulabo_api.db.models import CareEvent
from tsuyulabo_api.routers import brain, weeks

from .game_support import GameClient


async def test_decoder_output_is_recorded_once_and_remains_fresh(sessions):
    async with GameClient(sessions, brain.router, weeks.router) as game:
        week = (await game.post("/v1/weeks", {})).json()
        fly_id = week["id"]
        for _ in range(2):
            response = await game.get(f"/v1/flies/{fly_id}/behavior")
            assert response.status_code == 200
        async with sessions() as session:
            rows = list(
                await session.scalars(select(CareEvent).where(CareEvent.kind == "behaviour"))
            )
            assert len(rows) == 1
            assert rows[0].payload["behaviour"] == "walk"
            assert rows[0].payload["source"] == "brain_decoder"
        game.clock.advance(61)
        assert (await game.get(f"/v1/flies/{fly_id}/behavior")).status_code == 200
        async with sessions() as session:
            assert len(list(await session.scalars(select(CareEvent)))) == 2
