from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from tsuyulabo_api.app import create_app
from tsuyulabo_api.db.models import Base
from tsuyulabo_api.settings import Settings

from .game_support import FakeBrain, TestClock


async def test_application_registers_game_routes_and_inline_handler(tmp_path: Path) -> None:
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'app.db'}", _env_file=None),
        clock_source=TestClock(),
        brain_adapter=FakeBrain(),
    )
    async with app.state.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        guest = (
            await client.post(
                "/v1/auth/guest",
                json={"display_name": "test"},
                headers={"Idempotency-Key": str(uuid4())},
            )
        ).json()
        headers = {"Authorization": f"Bearer {guest['token']}"}
        week = (
            await client.post("/v1/weeks", headers=headers | {"Idempotency-Key": str(uuid4())})
        ).json()
        assert week["stage"] == "egg"
        response = await client.post(
            f"/v1/flies/{week['id']}/experiments",
            json={},
            headers=headers | {"Idempotency-Key": str(uuid4())},
        )
        job = (await client.get(f"/v1/jobs/{response.json()['job_id']}", headers=headers)).json()
        assert job["status"] == "succeeded"
        schema = (await client.get("/openapi.json")).json()
        assert all(
            path in schema["paths"]
            for path in (
                "/v1/home",
                "/v1/weeks/current/eclose",
                "/v1/puzzles/{puzzle_id}/submit",
                "/v1/adults/{adult_id}/level-up",
                "/v1/team/collect",
                "/v1/sleep/end",
                "/v1/friends/{friend_id}/gift",
                "/v1/zukan",
                "/v1/odds",
                "/v1/shiori/ask",
            )
        )
