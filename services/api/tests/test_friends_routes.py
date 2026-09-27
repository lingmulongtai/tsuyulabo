from __future__ import annotations

from typing import Any
from uuid import uuid4

from tsuyulabo_api.db.models import Friendship, User
from tsuyulabo_api.routers import friends, inventory, weeks
from tsuyulabo_api.services.ledger import add_material

from .game_support import GameClient


async def test_friendship_lab_like_gift_and_removal(sessions: Any) -> None:
    async with (
        GameClient(sessions, friends.router, inventory.router, weeks.router) as a,
        GameClient(sessions, friends.router, inventory.router, weeks.router) as b,
    ):
        friend_id = b.user["id"]
        assert (await a.get(f"/v1/friends/{friend_id}/lab")).status_code == 404
        assert (
            await a.post("/v1/friends", {"friend_code": a.user["friend_code"]})
        ).status_code == 422
        assert (await a.post("/v1/friends", {"friend_code": "BAD"})).status_code == 422
        assert (
            await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})
        ).status_code == 201
        assert len((await b.get("/v1/friends")).json()) == 1
        assert (await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})).json()[
            "error"
        ]["code"] == "already_friends"
        await b.post("/v1/weeks")
        assert (await a.get(f"/v1/friends/{friend_id}/lab")).json()["week"]["stage"] == "egg"
        assert (await a.post(f"/v1/friends/{friend_id}/like")).status_code == 200
        assert (await a.post(f"/v1/friends/{friend_id}/like")).status_code == 409
        gift_path = f"/v1/friends/{friend_id}/gift"
        assert (await a.post(gift_path, {"material": "banana", "amount": 6})).status_code == 422
        assert (await a.post(gift_path, {"material": "banana", "amount": 5})).json()["error"][
            "code"
        ] == "insufficient_funds"
        async with sessions() as session, session.begin():
            await add_material(session, a.user["id"], "banana", 10)
        key = str(uuid4())
        sent = await a.post(gift_path, {"material": "banana", "amount": 5}, key)
        assert sent.status_code == 200
        assert (
            await a.post(gift_path, {"material": "banana", "amount": 5}, key)
        ).json() == sent.json()
        assert (await a.post(gift_path, {"material": "banana", "amount": 1})).status_code == 409
        assert (await b.get("/v1/inventory")).json()["banana"] == 5
        assert (await a.get("/v1/me")).json()["balances"]["research_points"] == 10
        assert {n["kind"] for n in (await b.get("/v1/notifications")).json()} == {"like", "gift"}
        assert (await a.get("/v1/notifications")).json() == []
        await a.advance(to="next_day")
        assert (await a.post(f"/v1/friends/{friend_id}/like")).status_code == 200
        response = await a.client.delete(
            f"/v1/friends/{friend_id}", headers=a.headers | {"Idempotency-Key": str(uuid4())}
        )
        assert response.status_code == 200
        assert (await b.get("/v1/friends")).json() == []


async def test_friend_capacity_checks_both_users(sessions: Any) -> None:
    async with GameClient(sessions, friends.router) as a, GameClient(sessions, friends.router) as b:
        async with sessions() as session, session.begin():
            for index in range(50):
                other = User(display_name="friend", friend_code=f"TEST{index:04d}")
                session.add(other)
                await session.flush()
                session.add(Friendship(user_id=b.user["id"], friend_id=other.id))
        response = await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})
        assert response.json()["error"]["code"] == "friend_limit"
        assert (await a.get("/v1/friends")).json() == []
