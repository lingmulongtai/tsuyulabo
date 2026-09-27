from __future__ import annotations

from typing import Any

from tsuyu_shiori.gateway import MockProvider
from tsuyulabo_api.routers import puzzles, weeks
from tsuyulabo_api.services.shiori import perform
from tsuyulabo_api.services.shiori_store import SQLRecordStore

from .game_support import GameClient
from .puzzle_solvers import play


async def test_shiori_reads_nested_api_training_associations(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        week = (await game.post("/v1/weeks")).json()
        await game.advance(to="next_day")
        trained = await play(game, sessions, "training")
        async with sessions() as session, session.begin():
            record = await SQLRecordStore(session, game.user["id"]).association(
                week["id"], "banana"
            )
            assert record.data["value"] == trained["association"]["value"]
            answer = await perform(
                session, game.user["id"], {"question": "bananaのしつけは何回？"}, MockProvider()
            )
            assert "1回" in answer["answer"]
