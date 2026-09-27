from __future__ import annotations

from typing import Any

from tsuyulabo_api.db.models import ShioriMessage
from tsuyulabo_api.routers import home, puzzles, weeks

from .game_support import GameClient


async def test_home_aggregate_todo_and_memo(sessions: Any) -> None:
    async with GameClient(sessions, home.router, weeks.router, puzzles.router) as game:
        empty = (await game.get("/v1/home")).json()
        assert set(empty) == {
            "clock",
            "week",
            "fly",
            "todo",
            "balances",
            "team",
            "shiori",
            "circadian",
        }
        assert empty["circadian"] == {
            "gauge": 0,
            "streak": 0,
            "typical_bedtime": None,
            "typical_wake": None,
        }
        assert empty["week"] is None and empty["shiori"]["memo"] is None
        await game.post("/v1/weeks")
        response = (await game.get("/v1/home")).json()
        assert response["clock"]["research_day"] == 1
        assert response["fly"]["stage"] == "egg"
        assert next(t for t in response["todo"] if t["action"] == "training")["status"] == "locked"
        puzzle = (await game.post("/v1/puzzles", {"kind": "meal"})).json()
        await game.post(f"/v1/puzzles/{puzzle['puzzle_id']}/submit", {"moves": [], "elapsed_ms": 0})
        async with sessions() as session, session.begin():
            session.add(
                ShioriMessage(
                    user_id=game.user["id"],
                    role="memo",
                    text="memo",
                    evidence=["#0001"],
                    created_at=game.clock.now(),
                )
            )
        response = (await game.get("/v1/home")).json()
        assert next(t for t in response["todo"] if t["action"] == "meal")["status"] == "done"
        assert response["shiori"]["memo"]["evidence"] == ["#0001"]
        await game.advance(to="next_day")
        assert (await game.get("/v1/home")).json()["shiori"]["memo"] is None
