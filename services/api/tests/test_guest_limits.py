from __future__ import annotations

from typing import Any
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from tsuyulabo_api.db.models import User
from tsuyulabo_api.routers import users
from tsuyulabo_api.services.ratelimit import MemoryCounter, RateLimiter
from tsuyulabo_api.settings import Settings

from .http_support import router_app


async def test_guest_ip_global_cap_and_retry_same_key(sessions: Any) -> None:
    app = router_app(sessions, users.router)
    now = [100.0]
    app.state.settings = Settings(rate_guest_hour=1, rate_guest_day_global=2, _env_file=None)
    app.state.rate_limiter = RateLimiter(MemoryCounter(lambda: now[0]))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        async def guest(ip: str, key: str | None = None):
            return await client.post(
                "/v1/auth/guest",
                json={"display_name": "test"},
                headers={"Idempotency-Key": key or str(uuid4()), "X-Forwarded-For": ip},
            )

        assert (await guest("192.0.2.1")).status_code == 201
        key = str(uuid4())
        limited = await guest("192.0.2.1", key)
        assert limited.status_code == 429
        assert limited.headers["retry-after"] == "3500"
        assert (await guest("192.0.2.2")).status_code == 201
        assert (await guest("192.0.2.3")).headers["retry-after"] == "86300"
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(User)) == 2
        now[0] = 86400
        # Transient rejection did not claim/cache the idempotency key.
        assert (await guest("192.0.2.1", key)).status_code == 201


async def test_guest_redis_down_global_fallback_and_reads_open(sessions: Any) -> None:
    app = router_app(sessions, users.router)
    app.state.settings = Settings(rate_guest_fallback_hour_global=1, _env_file=None)
    app.state.rate_limiter = RateLimiter(None, MemoryCounter(lambda: 100))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post(
            "/v1/auth/guest",
            json={"display_name": "test"},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert first.status_code == 201
        blocked = await client.post(
            "/v1/auth/guest",
            json={"display_name": "test"},
            headers={"Idempotency-Key": str(uuid4()), "X-Forwarded-For": "192.0.2.2"},
        )
        assert blocked.status_code == 429
        auth = {"Authorization": f"Bearer {first.json()['token']}"}
        assert (await client.get("/v1/me", headers=auth)).status_code == 200
