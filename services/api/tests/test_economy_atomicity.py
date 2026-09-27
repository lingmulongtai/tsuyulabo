from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import func, select
from tsuyulabo_api.db.models import Adult, Gift, Inventory, LedgerAccount, LedgerEntry, Notification
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.routers import adults, friends
from tsuyulabo_api.services.ledger import add_material, verify_balance

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_gift_failure_rolls_back_materials_event_and_reward(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with GameClient(sessions, friends.router) as a, GameClient(sessions) as b:
        await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})
        async with sessions() as session, session.begin():
            await add_material(session, a.user["id"], "banana", 5)
        real_reward = friends.reward

        async def fail_after_reward(*args: Any, **kwargs: Any) -> None:
            await real_reward(*args, **kwargs)
            raise APIError("test_failure", "fail after ledger writes", 409)

        monkeypatch.setattr(friends, "reward", fail_after_reward)
        response = await a.post(
            f"/v1/friends/{b.user['id']}/gift", {"material": "banana", "amount": 5}
        )
        assert response.status_code == 409
        async with sessions() as session:
            assert (await session.get(Inventory, (a.user["id"], "banana"))).amount == 5
            assert await session.get(Inventory, (b.user["id"], "banana")) is None
            assert await session.scalar(select(func.count()).select_from(Gift)) == 0
            assert await session.scalar(select(func.count()).select_from(Notification)) == 0
            assert (
                await session.scalar(
                    select(func.count())
                    .select_from(LedgerEntry)
                    .where(LedgerEntry.reason == "friend_gift")
                )
                == 0
            )
            for account in await session.scalars(select(LedgerAccount)):
                assert await verify_balance(session, account.id)


async def test_level_up_failure_rolls_back_progress_and_debit(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with GameClient(sessions, adults.router) as game:
        adult_id = await make_adult(sessions, game, level=9)
        real_apply = adults.adults.apply_progress

        def fail_after_progress(*args: Any, **kwargs: Any) -> None:
            real_apply(*args, **kwargs)
            raise APIError("test_failure", "fail after level change", 409)

        monkeypatch.setattr(adults.adults, "apply_progress", fail_after_progress)
        assert (await game.post(f"/v1/adults/{adult_id}/level-up")).status_code == 409
        assert (await game.get("/v1/me")).json()["balances"]["shizuku"] == 300
        async with sessions() as session:
            adult = await session.get(Adult, adult_id)
            assert adult.level == 9 and adult.subskills == []
            assert (
                await session.scalar(
                    select(func.count())
                    .select_from(LedgerEntry)
                    .where(LedgerEntry.reason == "level_up")
                )
                == 0
            )
            for account in await session.scalars(select(LedgerAccount)):
                assert await verify_balance(session, account.id)
