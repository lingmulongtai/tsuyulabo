from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult, SleepSession
from tsuyulabo_api.routers import home, sleep, team

from .adult_fixtures import make_adult
from .game_support import GameClient
from .test_team_routes import put_team


async def seed_history(sessions: Any, game: GameClient, hours: float, count: int = 7) -> None:
    wake = game.clock.now().replace(hour=7)
    async with sessions() as session, session.begin():
        for days in range(1, count + 1):
            end = wake - timedelta(days=days)
            session.add(
                SleepSession(
                    user_id=game.user["id"], started_at=end - timedelta(hours=hours), ended_at=end
                )
            )


async def test_wake_bonus_home_consistency_and_replay(sessions: Any) -> None:
    async with GameClient(sessions, sleep.router, home.router) as game:
        await seed_history(sessions, game, 8)
        initial = (await game.get("/v1/home")).json()
        assert initial["week"] is None and initial["circadian"]["gauge"] == 100
        await game.advance(hours=19)  # 23:00 JST
        await game.post("/v1/sleep/start")
        await game.advance(hours=8)
        key = str(uuid4())
        response = await game.post("/v1/sleep/end", key=key)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["bonus"] == 220
        assert result["circadian"] == {
            "gauge": 100,
            "streak": 1,
            "typical_bedtime": "23:00",
            "typical_wake": "07:00",
        }  # Seed ends yesterday: the immediately preceding night is missing.
        assert (await game.get("/v1/home")).json()["circadian"] == result["circadian"]
        assert (await game.post("/v1/sleep/end", key=key)).json() == result
        assert (await game.post("/v1/sleep/end")).status_code == 409
        assert (await game.get("/v1/me")).json()["balances"]["shizuku"] == 520
        async with sessions() as session:
            record = await session.get(SleepSession, result["id"])
            assert record.bonus == 220


async def test_multiplier_affects_only_team_and_stacks_with_subskill(sessions: Any) -> None:
    async with GameClient(sessions, sleep.router, home.router, team.router) as game:
        await seed_history(sessions, game, 4)
        member = await make_adult(sessions, game, energy=0, subskills=["energy_up"])
        reserve = await make_adult(sessions, game, energy=10)
        await put_team(game, [member])
        await game.advance(hours=23)  # 03:00 the following calendar day, still night.
        await game.post("/v1/sleep/start")
        await game.advance(hours=4)
        response = await game.post("/v1/sleep/end")
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["circadian"]["gauge"] == 70
        assert result["bonus"] == 100
        assert result["energy_recovered"] == {member: pytest.approx(4 * 15 * 1.2 * 1.21)}
        async with sessions() as session:
            assert (await session.get(Adult, reserve)).energy == 10
            assert (await session.get(Adult, member)).energy == pytest.approx(87.12)


async def test_current_wake_can_cross_bonus_threshold(sessions: Any) -> None:
    async with GameClient(sessions, sleep.router, home.router) as game:
        await seed_history(sessions, game, 8, count=5)
        assert (await game.get("/v1/home")).json()["circadian"]["gauge"] == 71
        await game.advance(hours=19)
        await game.post("/v1/sleep/start")
        assert (await game.get("/v1/home")).json()["circadian"]["gauge"] == 71
        await game.advance(hours=8)
        result = (await game.post("/v1/sleep/end")).json()
        assert result["circadian"]["gauge"] == 86
        assert result["bonus"] == 220


async def test_home_isolates_users_and_ignores_active_future_and_invalid_records(
    sessions: Any,
) -> None:
    async with GameClient(sessions, home.router) as other:
        await seed_history(sessions, other, 8)
        async with GameClient(sessions, home.router) as game:
            now = game.clock.now()
            async with sessions() as session, session.begin():
                session.add_all(
                    [
                        SleepSession(user_id=game.user["id"], started_at=now),
                        SleepSession(
                            user_id=game.user["id"],
                            started_at=now,
                            ended_at=now + timedelta(hours=8),
                        ),
                        SleepSession(
                            user_id=game.user["id"],
                            started_at=now,
                            ended_at=now - timedelta(hours=1),
                        ),
                    ]
                )
            assert (await game.get("/v1/home")).json()["circadian"]["gauge"] == 0
            async with sessions() as session:
                assert len(list(await session.scalars(select(SleepSession)))) == 10
