from __future__ import annotations

from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.routers import jobs, users
from tsuyulabo_api.services.jobs import create_job

from .http_support import router_app


async def test_jobs_are_private(sessions: async_sessionmaker[AsyncSession]) -> None:
    app = router_app(sessions, users.router, jobs.router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        guests = []
        for name in ["owner", "other"]:
            guests.append(
                (
                    await client.post(
                        "/v1/auth/guest",
                        json={"display_name": name},
                        headers={"Idempotency-Key": str(uuid4())},
                    )
                ).json()
            )
        async with sessions() as session, session.begin():
            job = await create_job(session, guests[0]["user"]["id"], "learn")
        for guest, status in zip(guests, [200, 404], strict=True):
            response = await client.get(
                f"/v1/jobs/{job.id}", headers={"Authorization": f"Bearer {guest['token']}"}
            )
            assert response.status_code == status
            if status == 200:
                assert response.json()["status"] == "pending"
            else:
                assert response.json()["error"]["code"] == "not_found"
