from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from tsuyulabo_api.routers import users

from .http_support import router_app


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e999"])
async def test_nonfinite_json_is_rejected_before_validation(sessions: Any, number: str) -> None:
    app = router_app(sessions, users.router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/auth/guest",
            content='{"display_name":"test","ignored":' + number + "}",
            headers={"Idempotency-Key": str(uuid4()), "Content-Type": "application/json"},
        )
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "JSON の入力内容を確認してください"


async def test_streamed_body_is_bounded_without_content_length(sessions: Any) -> None:
    app = router_app(sessions, users.router)

    async def chunks() -> AsyncIterator[bytes]:
        yield b'{"display_name":"'
        for _ in range(17):
            yield b"x" * 4096
        yield b'"}'

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/auth/guest",
            content=chunks(),
            headers={"Idempotency-Key": str(uuid4()), "Content-Type": "application/json"},
        )
    assert response.status_code == 413


async def test_deep_json_returns_client_error(sessions: Any) -> None:
    app = router_app(sessions, users.router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/auth/guest",
            content="[" * 2000 + "0" + "]" * 2000,
            headers={"Idempotency-Key": str(uuid4()), "Content-Type": "application/json"},
        )
    assert response.status_code == 422
