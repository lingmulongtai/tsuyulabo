from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import CareEvent, LedgerAccount
from tsuyulabo_api.domain.team import material_weights
from tsuyulabo_api.routers import adults, friends, home, inventory, puzzles, sleep, team, weeks
from tsuyulabo_api.services import game as game_service
from tsuyulabo_api.services.ledger import verify_balance

from .game_support import GameClient
from .puzzle_solvers import play
from .test_team_routes import put_team


@pytest.mark.parametrize("real_engine", [False, pytest.param(True, marks=pytest.mark.eval)])
async def test_full_week_from_guest_to_collection_and_level_up(
    sessions: Any, monkeypatch: pytest.MonkeyPatch, real_engine: bool
) -> None:
    if real_engine:
        monkeypatch.setattr(game_service, "randbits", lambda bits: 42)
    routers = (
        weeks.router,
        puzzles.router,
        sleep.router,
        adults.router,
        team.router,
        inventory.router,
        home.router,
        friends.router,
    )
    async with (
        GameClient(sessions, *routers) as game,
        GameClient(sessions, friends.router) as friend,
    ):
        baseline = 0.0
        if real_engine:
            game.app.state.brain_adapter = engine = BrainAdapter()
            baseline = engine.preferences(engine.new())["banana"]
        assert (
            await game.post("/v1/friends", {"friend_code": friend.user["friend_code"]})
        ).status_code == 201
        assert (await game.post("/v1/weeks")).status_code == 201
        for day in range(1, 8):
            if day > 1:
                assert (await game.post("/v1/sleep/end")).status_code == 200
            for slot in ("morning", "noon", "night"):
                state = (await game.get("/v1/home")).json()
                assert state["clock"]["research_day"] == day
                assert state["clock"]["slot"] == slot
                await play(game, sessions, "meal")
                if day >= 2 and (not real_engine or day == 2):
                    trained = await play(game, sessions, "training")
                    assert trained["stars"] == 3
                if slot == "morning":
                    if day in (1, 6):
                        assert (await play(game, sessions, "temperature"))["score"] == 100
                    if 2 <= day <= 5:
                        assert (await play(game, sessions, "cleaning"))["score"] == 100
                if day == 5 and slot == "night":
                    assert (await play(game, sessions, "pupation_site"))["hit"]
                if slot != "night":
                    await game.advance(to="next_slot")
            if day < 7:
                assert (await game.post("/v1/sleep/start")).status_code == 200
                await game.advance(to="next_day")
        summary = (await game.get("/v1/weeks/current/presentation")).json()
        assert summary["rank"] in ("gold", "rainbow"), summary
        assert summary["care_miss"] <= 1  # Overnight starvation is charged once per week.
        eclosed = await game.post("/v1/weeks/current/eclose")
        assert eclosed.status_code == 200, eclosed.text
        adult = eclosed.json()["adult"]
        if real_engine:
            # Three ordinary 3-star puzzles use strength .36, not the engine eval's 1.0.
            assert adult["preferences"]["banana"] > baseline + 0.1
            weights = material_weights(adult["preferences"])
            assert weights["banana"] > material_weights({})["banana"]
        else:
            assert adult["preferences"]["banana"] > 0.6
            assert adult["skills"]["banana_search"]
        notification = (await friend.get("/v1/notifications")).json()[0]
        assert (
            notification["kind"] == "eclosion"
            and notification["payload"]["rank"] == summary["rank"]
        )
        assert (await put_team(game, [adult["id"]])).status_code == 200
        await game.advance(hours=8)
        collected = (await game.post("/v1/team/collect")).json()
        if real_engine:
            assert collected["materials"]["banana"] == max(collected["materials"].values())
        assert sum(collected["materials"].values()) == 12
        assert collected["team"]["members"][0]["level"] == 2
        level = await game.post(f"/v1/adults/{adult['id']}/level-up")
        assert level.status_code == 200 and level.json()["level"] == 3
        async with sessions() as session:
            events = list(
                await session.scalars(
                    select(CareEvent)
                    .where(CareEvent.user_id == game.user["id"])
                    .order_by(CareEvent.seq)
                )
            )
            assert [e.seq for e in events] == list(range(1, len(events) + 1))
            assert sum(e.kind == "meal" for e in events) == 21
            assert sum(e.kind == "training" for e in events) == (3 if real_engine else 18)
            for account in await session.scalars(select(LedgerAccount)):
                assert await verify_balance(session, account.id)


async def test_neglect_days_two_through_five_produces_normal_rank(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router) as game:
        await game.post("/v1/weeks")
        await play(game, sessions, "temperature")
        await play(game, sessions, "meal")
        for _ in range(5):
            await game.advance(to="next_day")
        await play(game, sessions, "temperature")
        await game.advance(to="eclosion")
        result = (await game.get("/v1/weeks/current/presentation")).json()
        assert result["care_miss"] == 18
        assert result["rank"] == "normal"
        repeated = (await game.get("/v1/weeks/current/presentation")).json()
        assert repeated == result
