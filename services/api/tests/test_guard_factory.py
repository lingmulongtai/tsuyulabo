from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from tsuyulabo_api.app import create_app
from tsuyulabo_api.db.models import Base
from tsuyulabo_api.services.ratelimit import MemoryCounter, RateLimiter
from tsuyulabo_api.settings import Settings


async def test_app_factory_wires_shared_limits_and_job_admission(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'guard.db'}",
            rate_guest_day_global=1,
            job_max_per_user=1,
            _env_file=None,
        ),
        rate_limiter=RateLimiter(MemoryCounter(lambda: 100)),
    )
    queue = AsyncMock()
    app.state.job_queue = queue
    async with app.state.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        first = await client.post(
            "/v1/auth/guest",
            json={"display_name": "test"},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert first.status_code == 201
        second = await client.post(
            "/v1/auth/guest",
            json={"display_name": "test"},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert second.status_code == 429
        assert second.headers["retry-after"] == "86300"
        auth = {"Authorization": f"Bearer {first.json()['token']}"}
        accepted = await client.post(
            "/v1/shiori/ask",
            json={"question": "なぜ？"},
            headers=auth | {"Idempotency-Key": str(uuid4())},
        )
        assert accepted.status_code == 202, accepted.text
        busy = await client.post(
            "/v1/shiori/ask",
            json={"question": "なぜ？"},
            headers=auth | {"Idempotency-Key": str(uuid4())},
        )
        assert busy.status_code == 503
        assert busy.headers["retry-after"] == "10"
        assert queue.enqueue.await_count == 1
