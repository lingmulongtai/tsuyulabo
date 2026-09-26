from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.routers import clock, dev, users

from .http_support import router_app


class FrozenClock:
    def now(self) -> datetime:
        return datetime(2026, 1, 1, 18, tzinfo=UTC)  # January 2, 03:00 JST.


async def test_clock_and_dev_advance(sessions: async_sessionmaker[AsyncSession]) -> None:
    app = router_app(sessions, users.router, clock.router, dev.router)
    app.state.clock = FrozenClock()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        guest = (
            await client.post(
                "/v1/auth/guest",
                json={"display_name": "test"},
                headers={"Idempotency-Key": str(uuid4())},
            )
        ).json()
        headers = {"Authorization": f"Bearer {guest['token']}"}
        initial = (await client.get("/v1/clock", headers=headers)).json()
        assert initial["server_now"] == initial["game_now"] == "2026-01-01T18:00:00+00:00"
        assert initial["slot"] == "night" and initial["day_boundary_hour"] == 4
        for body, offset, slot in [
            ({"to": "next_slot"}, 3600, "morning"),
            ({"hours": 8}, 9 * 3600, "noon"),
            ({"to": "next_day"}, 25 * 3600, "morning"),
        ]:
            response = await client.post(
                "/v1/dev/time/advance",
                json=body,
                headers=headers | {"Idempotency-Key": str(uuid4())},
            )
            assert response.status_code == 200
            assert response.json()["dev_time_offset_s"] == offset
            assert response.json()["slot"] == slot
            assert response.json()["server_now"] == initial["server_now"]
        assert (await client.get("/v1/dev/time", headers=headers)).json()[
            "dev_time_offset_s"
        ] == 90000
        for body in [{}, {"hours": -1}, {"hours": 1, "to": "next_day"}, {"hours": 1e300}]:
            invalid = await client.post(
                "/v1/dev/time/advance",
                json=body,
                headers=headers | {"Idempotency-Key": str(uuid4())},
            )
            assert invalid.status_code == 422
            assert invalid.json()["error"]["code"] == "validation_error"
        reset_headers = headers | {"Idempotency-Key": str(uuid4())}
        reset = await client.post("/v1/dev/time/reset", headers=reset_headers)
        assert reset.json()["dev_time_offset_s"] == 0
        app.state.settings.dev_tools = False
        for path, method in [
            ("/v1/dev/time", "GET"),
            ("/v1/dev/time/advance", "POST"),
            ("/v1/dev/time/reset", "POST"),
        ]:
            disabled = await client.request(method, path, headers=reset_headers)
            assert disabled.status_code == 403
            assert disabled.json()["error"]["code"] == "dev_tools_disabled"
