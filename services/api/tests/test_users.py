from __future__ import annotations

import asyncio
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.db.models import LedgerEntry, User
from tsuyulabo_api.routers.users import FRIEND_CODE_ALPHABET, router

from .http_support import router_app


async def test_guest_me_and_patch(sessions: async_sessionmaker[AsyncSession]) -> None:
    app = router_app(sessions, router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        key = {"Idempotency-Key": str(uuid4())}
        response = await client.post("/v1/auth/guest", json={"display_name": "ゆうき"}, headers=key)
        assert response.status_code == 201
        created = response.json()
        user = created["user"]
        assert len(user["friend_code"]) == 8
        assert set(user["friend_code"]) <= set(FRIEND_CODE_ALPHABET)
        assert user["balances"] == {"shizuku": 300, "research_points": 0, "kohaku": 0}
        repeated = await client.post("/v1/auth/guest", json={"display_name": "other"}, headers=key)
        assert repeated.status_code == 201 and repeated.json() == created
        auth = {"Authorization": f"Bearer {created['token']}"}
        assert (await client.get("/v1/me", headers=auth)).json() == user
        patch_headers = auth | {"Idempotency-Key": str(uuid4())}
        patch = await client.patch(
            "/v1/me", json={"display_name": "新しい名前", "title": "研究員"}, headers=patch_headers
        )
        assert patch.status_code == 200
        assert patch.json()["display_name"] == "新しい名前"
        assert patch.json()["title"] == "研究員"
        clear = await client.patch(
            "/v1/me", json={"title": None}, headers=auth | {"Idempotency-Key": str(uuid4())}
        )
        assert clear.status_code == 200 and clear.json()["title"] is None
        for body in [{"display_name": None}, {"display_name": " "}, {"dev_time_offset_s": 100}]:
            invalid = await client.patch(
                "/v1/me", json=body, headers=auth | {"Idempotency-Key": str(uuid4())}
            )
            assert invalid.status_code == 422
            assert invalid.json()["error"]["code"] == "validation_error"
        favorite = await client.patch(
            "/v1/me",
            json={"favorite_adult_id": str(uuid4())},
            headers=auth | {"Idempotency-Key": str(uuid4())},
        )
        assert favorite.status_code == 404
        for headers in [
            {},
            {"Authorization": "Bearer invalid"},
            {"Authorization": f"Bearer {app.state.auth_provider.issue_token('absent')}"},
        ]:
            rejected = await client.get("/v1/me", headers=headers)
            assert rejected.status_code == 401
            assert rejected.json()["error"]["code"] == "unauthorized"
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(User)) == 1
        assert await session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


async def test_concurrent_guest_registration(sessions: async_sessionmaker[AsyncSession]) -> None:
    app = router_app(sessions, router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Idempotency-Key": str(uuid4())}
        responses = await asyncio.gather(
            *[
                client.post("/v1/auth/guest", json={"display_name": "guest"}, headers=headers)
                for _ in range(3)
            ]
        )
        assert all(response.status_code == 201 for response in responses)
        assert len({response.json()["user"]["id"] for response in responses}) == 1
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(User)) == 1
