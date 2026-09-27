from __future__ import annotations

import base64
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.db.push import PushSubscription
from tsuyulabo_api.routers import push

from .game_support import GameClient


def subscription() -> dict:
    key = (
        ec.generate_private_key(ec.SECP256R1())
        .public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    )
    return {
        "endpoint": "https://fcm.googleapis.com/push/test",
        "expirationTime": None,
        "keys": {
            "p256dh": base64.urlsafe_b64encode(key).rstrip(b"=").decode(),
            "auth": base64.urlsafe_b64encode(b"a" * 16).rstrip(b"=").decode(),
        },
    }


async def test_subscription_ownership_retries_and_preferences(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with (
        GameClient(sessions, push.router) as owner,
        GameClient(sessions, push.router) as other,
    ):
        for game in (owner, other):
            game.app.state.settings.vapid_public_key = "test-public"
            game.app.state.settings.vapid_private_key = SecretStr("test-private")
        body = subscription()
        key = str(uuid4())
        for _ in range(2):
            assert (await owner.post("/v1/push/subscribe", body, key)).status_code == 200
        assert (await other.post("/v1/push/subscribe", body)).status_code == 409
        response = await other.client.request(
            "DELETE",
            "/v1/push/subscribe",
            json={"endpoint": body["endpoint"]},
            headers=other.headers | {"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == 200
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(PushSubscription)) == 1
        prefs = (await owner.get("/v1/push/preferences")).json()
        assert prefs["quiet_start"] == "23:00" and prefs["quiet_end"] == "07:00"
        prefs.update(meal_slots=["noon"], friend_activity=False)
        response = await owner.client.put(
            "/v1/push/preferences",
            json=prefs,
            headers=owner.headers | {"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == 200
        assert (await owner.get("/v1/push/preferences")).json() == prefs
        assert (await other.get("/v1/push/preferences")).json()["friend_activity"]
        response = await owner.client.request(
            "DELETE",
            "/v1/push/subscribe",
            json={"endpoint": body["endpoint"]},
            headers=owner.headers | {"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == 200
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(PushSubscription)) == 0


async def test_disabled_keys_auth_and_validation(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with GameClient(sessions, push.router) as game:
        assert (await game.client.get("/v1/push/public-key")).json() == {"public_key": None}
        assert (await game.client.get("/v1/push/preferences")).status_code == 401
        assert (await game.post("/v1/push/subscribe", subscription())).status_code == 503
        body = subscription()
        body["keys"]["auth"] = "bad"
        assert (await game.post("/v1/push/subscribe", body)).status_code == 422
        body = subscription()
        body["endpoint"] = "https://localhost/private"
        assert (await game.post("/v1/push/subscribe", body)).status_code == 422
        assert (
            await game.client.post("/v1/push/subscribe", json=subscription(), headers=game.headers)
        ).status_code == 400
