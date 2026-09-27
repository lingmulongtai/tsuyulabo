from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.auth.dependencies import get_current_user
from tsuyulabo_api.auth.provider import GuestAuthProvider
from tsuyulabo_api.db.models import IdempotencyKey, User
from tsuyulabo_api.db.session import get_session
from tsuyulabo_api.errors import APIError, exception_handler
from tsuyulabo_api.services.idempotency import IdempotentRoute


class FrozenClock:
    instant = datetime(2026, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self.instant


@pytest.fixture
async def harness(sessions: async_sessionmaker[AsyncSession]) -> tuple[FastAPI, dict[str, str]]:
    app = FastAPI()
    app.state.session_factory = sessions
    app.state.clock = FrozenClock()
    app.state.auth_provider = GuestAuthProvider("test-secret-with-at-least-32-characters")
    app.add_exception_handler(APIError, exception_handler)
    router = APIRouter(route_class=IdempotentRoute)

    @router.post("/other")
    @router.put("/increment")
    @router.post("/increment")
    async def increment(
        user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_session)],
        fail: bool = False,
    ) -> dict[str, int]:
        user.dev_time_offset_s += 1
        await session.flush()
        if fail:
            raise APIError("test_failure", "failure", 409)
        return {"value": user.dev_time_offset_s}

    app.include_router(router)
    async with sessions() as session, session.begin():
        user = User(display_name="test", friend_code="ABCDEFGH")
        session.add(user)
        await session.flush()
        token = app.state.auth_provider.issue_token(user.id)
    return app, {"Authorization": f"Bearer {token}"}


async def test_replay_missing_key_and_concurrent_duplicates(harness: tuple) -> None:
    app, headers = harness
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        missing = await client.post("/increment", headers=headers)
        assert missing.status_code == 400
        assert missing.json()["error"]["code"] == "idempotency_key_required"
        invalid = await client.post("/increment", headers=headers | {"Idempotency-Key": "bad"})
        assert invalid.status_code == 422
        headers = headers | {"Idempotency-Key": str(uuid4())}
        responses = await asyncio.gather(
            *[client.post("/increment", headers=headers) for _ in range(5)]
        )
        assert [response.json() for response in responses] == [{"value": 1}] * 5
        assert all(response.status_code == 200 for response in responses)


async def test_failures_rollback_replay_and_expire(harness: tuple) -> None:
    app, headers = harness
    headers = headers | {"Idempotency-Key": str(uuid4())}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/increment?fail=true", headers=headers)
        repeated = await client.post("/increment?fail=true", headers=headers)
        assert first.status_code == repeated.status_code == 409
        assert first.json() == repeated.json()
        async with app.state.session_factory() as session:
            assert await session.scalar(select(User.dev_time_offset_s)) == 0
        app.state.clock.instant += timedelta(hours=24)
        success = await client.post("/increment", headers=headers)
        assert success.json() == {"value": 1}
        async with app.state.session_factory() as session:
            assert await session.scalar(select(func.count()).select_from(IdempotencyKey)) == 1


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/increment", {"amount": 2}),
        ("POST", "/other", {"amount": 1}),
        ("PUT", "/increment", {"amount": 1}),
        ("POST", "/increment?fail=true", {"amount": 1}),
    ],
)
async def test_reused_key_binds_entire_request(
    harness: tuple, method: str, path: str, body: dict
) -> None:
    app, headers = harness
    headers = headers | {"Idempotency-Key": str(uuid4())}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (
            await client.post("/increment", json={"amount": 1}, headers=headers)
        ).status_code == 200
        changed = await client.request(method, path, json=body, headers=headers)
        assert changed.status_code == 409
        assert changed.json()["error"]["code"] == "idempotency_key_reused"
        async with app.state.session_factory() as session:
            assert await session.scalar(select(User.dev_time_offset_s)) == 1


async def test_concurrent_different_bodies_and_user_scopes(harness: tuple) -> None:
    app, headers = harness
    headers = headers | {"Idempotency-Key": str(uuid4())}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        responses = await asyncio.gather(
            *[client.post("/increment", json={"amount": i}, headers=headers) for i in range(2)]
        )
        assert sorted(r.status_code for r in responses) == [200, 409]
        async with app.state.session_factory() as session, session.begin():
            other = User(display_name="other", friend_code="OTHER123")
            session.add(other)
            await session.flush()
            token = app.state.auth_provider.issue_token(other.id)
        other_headers = headers | {"Authorization": f"Bearer {token}"}
        response = await client.post("/increment", json={"amount": 3}, headers=other_headers)
        assert response.status_code == 200 and response.json() == {"value": 1}


@pytest.mark.parametrize("legacy", [False, True])
async def test_pending_and_legacy_records_do_not_replay_different_request(
    harness: tuple, legacy: bool
) -> None:
    app, headers = harness
    key = str(uuid4())
    headers = headers | {"Idempotency-Key": key}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/increment", json={"amount": 1}, headers=headers)
        async with app.state.session_factory() as session, session.begin():
            record = await session.scalar(select(IdempotencyKey).where(IdempotencyKey.key == key))
            if legacy:
                record.path = "/increment"
            else:
                record.status_code = 0
                record.response = {"status": 200, "body": {"value": 1}}
        response = await client.post("/increment", json={"amount": 2}, headers=headers)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "idempotency_key_reused"
