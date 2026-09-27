from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from tsuyulabo_api.app import create_app
from tsuyulabo_api.settings import Settings

from .game_support import TestClock


def app_for(sessions: Any, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SHIORI_PROVIDER", "mock")
    return create_app(
        Settings(
            database_url=str(sessions.kw["bind"].url),
            brain_mode="inline",
            dev_tools=True,
            _env_file=None,
        ),
        clock_source=TestClock(),
    )


async def ask(client: AsyncClient, auth: dict[str, str], question: str) -> dict[str, Any]:
    response = await client.post(
        "/v1/shiori/ask",
        json={"question": question},
        headers=auth | {"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 202, response.text
    job = await client.get(f"/v1/jobs/{response.json()['job_id']}", headers=auth)
    return job.json()


async def guest(client: AsyncClient) -> dict[str, str]:
    created = await client.post(
        "/v1/auth/guest", json={"display_name": "test"}, headers={"Idempotency-Key": str(uuid4())}
    )
    return {"Authorization": f"Bearer {created.json()['token']}"}


async def test_question_before_the_first_egg_gets_a_gentle_answer(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = app_for(sessions, monkeypatch)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        auth = await guest(client)
        job = await ask(client, auth, "ツユの脳はどう変わるの？")
        assert job["status"] == "succeeded", job
        assert job["result"]["evidence"] == []
        assert "記録" in job["result"]["answer"]


async def test_question_after_eclosion_uses_the_latest_week(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = app_for(sessions, monkeypatch)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        auth = await guest(client)
        headers = lambda: auth | {"Idempotency-Key": str(uuid4())}  # noqa: E731
        assert (await client.post("/v1/weeks", headers=headers())).status_code == 201
        advanced = await client.post(
            "/v1/dev/time/advance", json={"to": "eclosion"}, headers=headers()
        )
        assert advanced.status_code == 200, advanced.text
        eclosed = await client.post("/v1/weeks/current/eclose", headers=headers())
        assert eclosed.status_code == 200, eclosed.text
        job = await ask(client, auth, "しつけをすると、ツユの脳はどう変わるの？")
        assert job["status"] == "succeeded", job
        assert job["result"]["answer"]
