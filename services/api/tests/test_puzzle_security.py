from __future__ import annotations

import asyncio
from random import Random
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from tsuyulabo_api.db.models import CareEvent, LarvaState, Puzzle
from tsuyulabo_api.domain.puzzles import meal
from tsuyulabo_api.routers import puzzles, weeks

from .game_support import GameClient


def test_meal_rejects_excess_moves_before_iterating() -> None:
    params, _ = meal.generate(Random(0), {})
    result = meal.verify(params, {"moves": [{}] * 91, "elapsed_ms": 0})
    assert not result.valid and result.reason == "wrong_length"


@pytest.mark.parametrize("field,length", [("moves", 91), ("path", 37), ("taps", 4)])
async def test_excess_action_counts_do_not_record_care(
    sessions: Any, field: str, length: int
) -> None:
    kind = {"moves": "meal", "path": "training", "taps": "cleaning"}[field]
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        await game.post("/v1/weeks")
        await game.advance(to="next_day")
        issued = await game.post(
            "/v1/puzzles", {"kind": kind, "cue": "banana", "valence": "reward"}
        )
        puzzle_id = issued.json()["puzzle_id"]
        values = [{}] * length if field == "moves" else [0] * length
        response = await game.post(
            f"/v1/puzzles/{puzzle_id}/submit", {field: values, "elapsed_ms": 0}
        )
        assert response.status_code == 422
        async with sessions() as session:
            assert (await session.get(Puzzle, puzzle_id)).submitted_at is None
            assert await session.scalar(select(func.count()).select_from(CareEvent)) == 0


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e999"])
async def test_nonfinite_submission_does_not_create_an_event(sessions: Any, number: str) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        await game.post("/v1/weeks")
        issued = (await game.post("/v1/puzzles", {"kind": "meal"})).json()
        response = await game.client.post(
            f"/v1/puzzles/{issued['puzzle_id']}/submit",
            content='{"moves":[],"elapsed_ms":0,"score":' + number + "}",
            headers=game.headers
            | {"Idempotency-Key": str(uuid4()), "Content-Type": "application/json"},
        )
        assert response.status_code == 422
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(CareEvent)) == 0


async def test_concurrent_submission_ignores_forged_score_and_effects(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        week = (await game.post("/v1/weeks")).json()
        issued = (await game.post("/v1/puzzles", {"kind": "meal"})).json()
        body = {
            "moves": [],
            "elapsed_ms": 0,
            "score": 10**12,
            "effects": {"growth": 10**12},
            "submitted_at": "2099-01-01T00:00:00Z",
        }
        responses = await asyncio.gather(
            *[game.post(f"/v1/puzzles/{issued['puzzle_id']}/submit", body) for _ in range(2)]
        )
        assert sorted(r.status_code for r in responses) == [200, 409]
        success = next(r.json() for r in responses if r.status_code == 200)
        assert success["score"] == 0 and success["effects"]["growth"] == 0
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(CareEvent)) == 1
            assert (await session.get(LarvaState, week["id"])).growth == 0
