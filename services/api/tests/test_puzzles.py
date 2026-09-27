from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from tsuyulabo_api.db.models import CareEvent, LarvaState, Puzzle
from tsuyulabo_api.routers import puzzles, weeks

from .game_support import GameClient


async def test_submit_validation_quota_and_replay(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        await game.post("/v1/weeks")
        issued = await game.post("/v1/puzzles", {"kind": "meal"})
        assert issued.status_code == 201
        assert "secret" not in issued.json()
        path = f"/v1/puzzles/{issued.json()['puzzle_id']}/submit"
        invalid = await game.post(
            path, {"moves": [{"p": 50, "r": 0, "c": 0, "t": 0}], "elapsed_ms": 0}
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["details"]["reason"] == "not_in_hand"
        body = {"moves": [{"p": 0, "r": 0, "c": 0, "t": 5000}], "elapsed_ms": 5000}
        assert (await game.post(path, body)).json()["error"]["details"]["reason"] == "time_exceeded"
        game.clock.advance(5)
        key = str(uuid4())
        success = await game.post(path, body, key)
        assert success.status_code == 200, success.text
        assert (await game.post(path, body, key)).json() == success.json()
        assert (await game.post(path, body)).json()["error"]["code"] == "puzzle_already_submitted"
        assert (await game.post("/v1/puzzles", {"kind": "meal"})).json()["error"][
            "code"
        ] == "slot_already_used"
        async with sessions() as session:
            events = (await session.scalars(select(CareEvent))).all()
            assert len(events) == 1 and events[0].seq == 1
        unavailable = await game.post(
            "/v1/puzzles", {"kind": "training", "cue": "banana", "valence": "reward"}
        )
        assert unavailable.json()["error"]["code"] == "not_available_today"


async def test_training_limits_learning_and_ownership(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        week = (await game.post("/v1/weeks")).json()
        await game.advance(to="next_day")
        request = {"kind": "training", "cue": "banana", "valence": "reward"}
        for _ in range(3):
            issued = (await game.post("/v1/puzzles", request)).json()
            async with sessions() as session:
                puzzle = await session.get(Puzzle, issued["puzzle_id"])
                body = {"path": puzzle.secret["path"], "elapsed_ms": 5000}
            game.clock.advance(5)
            response = await game.post(f"/v1/puzzles/{puzzle.id}/submit", body)
            assert response.status_code == 200, response.text
            assert response.json()["stars"] == 3
        assert (await game.post("/v1/puzzles", request)).json()["error"][
            "code"
        ] == "daily_limit_reached"
        async with sessions() as session:
            state = await session.get(LarvaState, week["id"])
            assert state.skills["banana_search"]
            assert len(state.brain_snapshot["training"]) == 3
        async with GameClient(sessions, puzzles.router) as other:
            assert (await other.post(f"/v1/puzzles/{puzzle.id}/submit", body)).status_code == 404


async def test_expiry_and_multiple_issued_puzzles(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        await game.post("/v1/weeks")
        first = (await game.post("/v1/puzzles", {"kind": "meal"})).json()
        second = (await game.post("/v1/puzzles", {"kind": "meal"})).json()
        body = {"moves": [], "elapsed_ms": 0}
        assert (
            await game.post(f"/v1/puzzles/{first['puzzle_id']}/submit", body)
        ).status_code == 200
        assert (
            await game.post(f"/v1/puzzles/{second['puzzle_id']}/submit", body)
        ).status_code == 409
        await game.advance(to="next_slot")
        third = (await game.post("/v1/puzzles", {"kind": "meal"})).json()
        game.clock.advance(600)
        expired = await game.post(f"/v1/puzzles/{third['puzzle_id']}/submit", body)
        assert expired.json()["error"]["code"] == "puzzle_expired"
