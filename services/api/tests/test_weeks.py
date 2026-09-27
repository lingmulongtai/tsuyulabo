from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from tsuyulabo_api.db.models import Adult, CareEvent, LarvaState, LedgerAccount
from tsuyulabo_api.routers import weeks
from tsuyulabo_api.services.ledger import verify_balance

from .game_support import GameClient


async def test_week_lifecycle_and_lazy_misses(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router) as game:
        assert (await game.get("/v1/weeks/current")).status_code == 409
        started = await game.post("/v1/weeks")
        assert started.status_code == 201
        week_id = started.json()["id"]
        assert started.json()["stage"] == "egg"
        assert len(started.json()["days"]) == 7
        assert (await game.post("/v1/weeks")).json()["error"]["code"] == "week_already_active"
        assert (await game.get("/v1/weeks/current/presentation")).status_code == 409
        assert (await game.post("/v1/weeks/current/eclose")).status_code == 409
        await game.advance(to="eclosion")
        first = (await game.get("/v1/weeks/current")).json()
        second = (await game.get("/v1/weeks/current")).json()
        assert first == second
        assert first["care_miss"] == 20
        summary = (await game.get("/v1/weeks/current/presentation")).json()
        assert summary["rank"] == "normal"
        async with sessions() as session, session.begin():
            state = await session.get(LarvaState, week_id)
            assert len(state.miss_keys) == 20
            session.add(
                CareEvent(
                    user_id=game.user["id"],
                    week_id=week_id,
                    seq=2,
                    kind="meal",
                    research_day=1,
                    slot="morning",
                    score=30000,
                    payload={},
                    created_at=game.clock.now(),
                )
            )
        key = str(uuid4())
        eclosed = await game.post("/v1/weeks/current/eclose", key=key)
        assert eclosed.status_code == 200, eclosed.text
        assert (await game.post("/v1/weeks/current/eclose", key=key)).json() == eclosed.json()
        assert eclosed.json()["omen_sequence"][-1] == eclosed.json()["tier"]
        assert len((await game.get("/v1/weeks")).json()) == 1
        async with sessions() as session:
            assert len((await session.scalars(select(Adult))).all()) == 1
            for account in await session.scalars(select(LedgerAccount)):
                assert await verify_balance(session, account.id)
        assert (await game.post("/v1/weeks")).status_code == 201


async def test_week_requires_idempotency(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router) as game:
        response = await game.client.post("/v1/weeks", headers=game.headers)
        assert response.status_code == 400
