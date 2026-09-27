from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select
from tsuyulabo_api.db.models import DailyCircuitAttempt, LedgerAccount, LedgerEntry, User
from tsuyulabo_api.domain.clock import JST
from tsuyulabo_api.domain.puzzles.daily_circuit import generate
from tsuyulabo_api.routers import daily_circuit, friends
from tsuyulabo_api.services.ledger import verify_balance

from .adult_fixtures import make_adult
from .game_support import GameClient

BASE = "/v1/daily-circuit"


def solution(day: str, elapsed_ms: int = 10000) -> dict:
    _, secret = generate(date.fromisoformat(day))
    return {"day": day, "path": secret["path"], "elapsed_ms": elapsed_ms}


async def test_shared_board_changes_at_four_not_midnight_or_dev_offset(sessions: Any) -> None:
    async with (
        GameClient(sessions, daily_circuit.router) as a,
        GameClient(sessions, daily_circuit.router) as b,
    ):
        a.clock.value = b.clock.value = datetime(2026, 1, 6, 0, tzinfo=JST)
        first = (await a.get(BASE)).json()
        assert first["attempt"] is first["my_result"] is None
        assert first["day"] == "2026-01-05"
        await b.advance(hours=48)
        assert (await b.get(BASE)).json()["params"] == first["params"]
        a.clock.value = datetime(2026, 1, 6, 3, 59, 59, tzinfo=JST)
        assert (await a.get(BASE)).json()["params"] == first["params"]
        a.clock.advance(1)
        second = (await a.get(BASE)).json()
        assert second["day"] == "2026-01-06"
        assert second["params"] != first["params"]
        async with sessions() as session:
            assert (await session.scalars(select(DailyCircuitAttempt))).all() == []


async def test_start_resume_submit_replay_and_ledger(sessions: Any) -> None:
    async with GameClient(sessions, daily_circuit.router) as game:
        day = (await game.get(BASE)).json()["day"]
        assert (await game.post(f"{BASE}/submit", solution(day))).status_code == 404
        started = (await game.post(f"{BASE}/start", {"day": day})).json()
        game.clock.advance(10)
        resumed = (await game.post(f"{BASE}/start", {"day": day})).json()
        assert resumed["attempt"] == started["attempt"]
        key = str(uuid4())
        response = await game.post(f"{BASE}/submit", solution(day), key)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["elapsed_ms"] == 10000
        assert result["shizuku"] == 60
        game.clock.advance(1)
        assert (await game.post(f"{BASE}/submit", solution(day), key)).json() == result
        assert (await game.post(f"{BASE}/submit", solution(day, 1))).json() == result
        assert (await game.get(BASE)).json()["my_result"] == result
        assert (await game.get("/v1/me")).json()["balances"]["shizuku"] == 360
        async with sessions() as session:
            entries = list(
                await session.scalars(
                    select(LedgerEntry).where(LedgerEntry.reason == "daily_circuit")
                )
            )
            assert len(entries) == 2 and sum(e.amount for e in entries) == 0
            for account in await session.scalars(select(LedgerAccount)):
                assert await verify_balance(session, account.id)


@pytest.mark.parametrize("seconds,reward", [(19.999, 60), (20, 40), (39.999, 40), (40, 20)])
async def test_server_elapsed_prevents_forged_fast_rewards(
    sessions: Any, seconds: float, reward: int
) -> None:
    async with GameClient(sessions, daily_circuit.router) as game:
        day = (await game.get(BASE)).json()["day"]
        await game.post(f"{BASE}/start", {"day": day})
        game.clock.advance(seconds)
        response = await game.post(f"{BASE}/submit", solution(day, 0))
        assert response.status_code == 200
        assert response.json()["elapsed_ms"] == int(seconds * 1000)
        assert response.json()["shizuku"] == reward


async def test_invalid_paths_and_time_do_not_consume_result(sessions: Any) -> None:
    async with GameClient(sessions, daily_circuit.router) as game:
        day = (await game.get(BASE)).json()["day"]
        await game.post(f"{BASE}/start", {"day": day})
        good = solution(day, 10000)
        for bad in (
            good,  # More than the wall-clock grace ahead of the server.
            good | {"path": [0] * 49},
            good | {"path": list(reversed(good["path"]))},
            good | {"path": [True] + good["path"][1:]},
            good | {"elapsed_ms": -1},
            good | {"elapsed_ms": 1.5},
        ):
            assert (await game.post(f"{BASE}/submit", bad)).status_code == 422
        assert (await game.get(BASE)).json()["my_result"] is None
        assert (await game.get(f"{BASE}/ranking")).json()["entries"] == []
        game.clock.advance(8)
        assert (await game.post(f"{BASE}/submit", good)).status_code == 200


async def test_expiry_and_rollover_cannot_restart_attempt(sessions: Any) -> None:
    async with GameClient(sessions, daily_circuit.router) as game:
        day = (await game.get(BASE)).json()["day"]
        started = (await game.post(f"{BASE}/start", {"day": day})).json()
        game.clock.advance(600)
        assert (await game.post(f"{BASE}/submit", solution(day))).status_code == 409
        assert (await game.post(f"{BASE}/start", {"day": day})).json()["attempt"] == started[
            "attempt"
        ]
        game.clock.value = datetime(2026, 1, 6, 3, 59, 59, tzinfo=JST)
        game.clock.advance(1)
        assert (await game.post(f"{BASE}/submit", solution(day))).status_code == 409
        assert (await game.post(f"{BASE}/start", {"day": day})).status_code == 409
        today = (await game.get(BASE)).json()
        assert today["attempt"] is today["my_result"] is None
        assert (await game.post(f"{BASE}/start", {"day": today["day"]})).status_code == 200


async def test_attempt_near_boundary_expires_at_boundary(sessions: Any) -> None:
    async with GameClient(sessions, daily_circuit.router) as game:
        game.clock.value = datetime(2026, 1, 6, 3, 59, 59, tzinfo=JST)
        response = (await game.post(f"{BASE}/start", {"day": "2026-01-05"})).json()
        assert datetime.fromisoformat(response["attempt"]["expires_at"]) == datetime(
            2026, 1, 6, 4, tzinfo=JST
        )


async def test_concurrent_starts_and_submissions_reward_once(sessions: Any) -> None:
    async with GameClient(sessions, daily_circuit.router) as game:
        day = (await game.get(BASE)).json()["day"]
        starts = await asyncio.gather(*(game.post(f"{BASE}/start", {"day": day}) for _ in range(2)))
        assert all(r.status_code == 200 for r in starts)
        assert starts[0].json()["attempt"] == starts[1].json()["attempt"]
        game.clock.advance(10)
        results = await asyncio.gather(
            *(game.post(f"{BASE}/submit", solution(day)) for _ in range(2))
        )
        assert all(r.status_code == 200 for r in results)
        assert results[0].json() == results[1].json()
        assert (await game.get("/v1/me")).json()["balances"]["shizuku"] == 360


async def test_ranking_is_private_sorted_and_uses_favorite_art(sessions: Any) -> None:
    async with (
        GameClient(sessions, daily_circuit.router, friends.router) as a,
        GameClient(sessions, daily_circuit.router) as b,
        GameClient(sessions, daily_circuit.router) as outsider,
    ):
        await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})
        adult_id = await make_adult(sessions, b, strain="curly", sex="m")
        async with sessions() as session, session.begin():
            person = await session.get(User, b.user["id"])
            person.favorite_adult_id = adult_id
        # Same elapsed time; b submits earlier, despite a being the requesting user.
        for game, delay, seconds in ((b, 0, 10), (a, 5, 10), (outsider, 0, 5)):
            game.clock.advance(delay)
            day = (await game.get(BASE)).json()["day"]
            await game.post(f"{BASE}/start", {"day": day})
            game.clock.advance(seconds)
            assert (
                await game.post(f"{BASE}/submit", solution(day, seconds * 1000))
            ).status_code == 200
        ranking = (await a.get(f"{BASE}/ranking")).json()["entries"]
        assert [entry["user_id"] for entry in ranking] == [b.user["id"], a.user["id"]]
        assert [entry["rank"] for entry in ranking] == [1, 2]
        assert ranking[0]["avatar"] == {"strain": "curly", "sex": "m"}
        assert ranking[1]["avatar"]["strain"] == "wild"
        assert [entry["is_me"] for entry in ranking] == [False, True]
        await a.client.delete(
            f"/v1/friends/{b.user['id']}", headers=a.headers | {"Idempotency-Key": str(uuid4())}
        )
        assert len((await a.get(f"{BASE}/ranking")).json()["entries"]) == 1
        a.clock.advance(86400)
        assert (await a.get(f"{BASE}/ranking")).json()["entries"] == []


async def test_auth_and_idempotency_are_required(sessions: Any) -> None:
    async with GameClient(sessions, daily_circuit.router) as game:
        assert (await game.client.get(BASE)).status_code == 401
        assert (await game.client.get(f"{BASE}/ranking")).status_code == 401
        assert (
            await game.client.post(
                f"{BASE}/start", json={"day": "2026-01-05"}, headers=game.headers
            )
        ).status_code == 400
