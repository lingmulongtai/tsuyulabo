from __future__ import annotations

from typing import Any

from tsuyulabo_api.db.models import Adult, Week
from tsuyulabo_api.services.brain_state import store

from .game_support import GameClient


async def make_adult(sessions: Any, game: GameClient, **overrides: Any) -> str:
    async with sessions() as session, session.begin():
        week = Week(user_id=game.user["id"], status="eclosed", started_at=game.clock.now())
        session.add(week)
        await session.flush()
        values = dict(
            user_id=game.user["id"],
            week_id=week.id,
            name="test",
            stars=3,
            sex="f",
            strain="wild",
            brain_snapshot=game.app.state.brain_adapter.new(),
        )
        adult = Adult(**(values | overrides))
        store(adult, adult.brain_snapshot, game.app.state.brain_adapter)
        if "preferences" in overrides:
            adult.preferences = overrides["preferences"]
        session.add(adult)
        await session.flush()
        return adult.id
