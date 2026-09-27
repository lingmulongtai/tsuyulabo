from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from tsuyulabo_api.app import create_app
from tsuyulabo_api.db.models import Experiment, ShioriMessage
from tsuyulabo_api.settings import Settings

from .game_support import TestClock


async def test_default_inline_ask_returns_mock_answer_with_real_experiment(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SHIORI_PROVIDER", "mock")
    app = create_app(
        Settings(database_url=str(sessions.kw["bind"].url), brain_mode="inline", _env_file=None),
        clock_source=TestClock(),
    )
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        guest = await client.post(
            "/v1/auth/guest",
            json={"display_name": "test"},
            headers={"Idempotency-Key": str(uuid4())},
        )
        auth = {"Authorization": f"Bearer {guest.json()['token']}"}
        started = await client.post("/v1/weeks", headers=auth | {"Idempotency-Key": str(uuid4())})
        assert started.status_code == 201
        headers = auth | {"Idempotency-Key": str(uuid4())}
        response = await client.post(
            "/v1/shiori/ask", json={"question": "bananaの好みを実験して"}, headers=headers
        )
        assert response.status_code == 202, response.text
        job = (await client.get(f"/v1/jobs/{response.json()['job_id']}", headers=auth)).json()
        assert job["status"] == "succeeded", job
        assert job["result"]["answer"] and job["result"]["experiments"]
        assert job["result"]["cost"]["usd"] == 0
        repeated = await client.post(
            "/v1/shiori/ask", json={"question": "bananaの好みを実験して"}, headers=headers
        )
        assert repeated.json() == response.json()
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(ShioriMessage)) == 2
            assert await session.scalar(select(func.count()).select_from(Experiment)) == 1
