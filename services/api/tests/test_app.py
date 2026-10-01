from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from tsuyulabo_api.app import create_app
from tsuyulabo_api.services.jobs import ArqJobQueue, InlineJobQueue
from tsuyulabo_api.settings import Settings


async def test_factory_health_errors_cors_and_routes(engine: AsyncEngine) -> None:
    app = create_app(Settings(database_url=str(engine.url), _env_file=None))
    assert isinstance(app.state.job_queue, InlineJobQueue)

    @app.get("/test-failure")
    async def fail() -> None:
        raise RuntimeError("private database credentials")

    async with (
        app.router.lifespan_context(app),
        AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
        ) as client,
    ):
        health = await client.get("/healthz")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "database": "ok", "redis": "disabled"}
        app.state.redis = AsyncMock()
        app.state.redis.ping.side_effect = ConnectionError("secret")
        degraded = await client.get("/healthz")
        assert degraded.status_code == 503 and degraded.json()["redis"] == "error"
        assert "secret" not in degraded.text
        for path, status, code in [
            ("/missing", 404, "not_found"),
            ("/v1/me", 401, "unauthorized"),
            ("/test-failure", 500, "internal_error"),
        ]:
            response = await client.get(path)
            assert response.status_code == status
            assert response.json()["error"]["code"] == code
            assert set(response.json()["error"]) == {"code", "message", "details"}
            assert "private" not in response.text
        bad = await client.post(
            "/v1/auth/guest", json={}, headers={"Idempotency-Key": str(uuid4())}
        )
        assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation_error"
        guest = await client.post(
            "/v1/auth/guest",
            json={"display_name": "test"},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert guest.status_code == 201
        auth = {"Authorization": f"Bearer {guest.json()['token']}"}
        assert (await client.get("/v1/me", headers=auth)).status_code == 200
        assert (await client.get("/v1/clock", headers=auth)).status_code == 200
        assert (await client.get("/v1/dev/time", headers=auth)).status_code == 403
        assert (await client.get("/v1/jobs/absent", headers=auth)).status_code == 404
        cors = await client.options(
            "/v1/me",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "Idempotency-Key",
            },
        )
        assert cors.status_code == 200
        assert cors.headers["access-control-allow-origin"] == "http://localhost:3000"
        # Tailnet devices resolve the self-hosted API to a private address, so Chrome asks first.
        private = await client.options(
            "/v1/auth/guest",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Idempotency-Key",
                "Access-Control-Request-Private-Network": "true",
            },
        )
        assert private.status_code == 200
        assert private.headers["access-control-allow-private-network"] == "true"
        foreign = await client.options(
            "/v1/auth/guest",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Private-Network": "true",
            },
        )
        assert foreign.status_code == 400
        schema = (await client.get("/openapi.json")).json()
        assert "/v1/auth/guest" in schema["paths"]


async def test_queue_configuration(engine: AsyncEngine) -> None:
    with pytest.raises(ValueError, match="REDIS_URL"):
        create_app(Settings(brain_mode="queue", _env_file=None))
    app = create_app(
        Settings(
            database_url=str(engine.url),
            brain_mode="queue",
            redis_url="redis://localhost:6379/0",
            _env_file=None,
        )
    )
    async with app.router.lifespan_context(app):
        assert isinstance(app.state.job_queue, ArqJobQueue)
