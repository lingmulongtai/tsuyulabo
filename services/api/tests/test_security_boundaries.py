from __future__ import annotations

from typing import Any
from uuid import uuid4

from tsuyulabo_api.db.models import Job
from tsuyulabo_api.routers import adults, brain, daily_circuit, friends, jobs, puzzles, team, weeks

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_friendship_does_not_grant_owner_routes(sessions: Any) -> None:
    routers = (
        adults.router,
        brain.router,
        friends.router,
        jobs.router,
        puzzles.router,
        team.router,
        weeks.router,
        daily_circuit.router,
    )
    async with GameClient(sessions, *routers) as a, GameClient(sessions, *routers) as b:
        adult_id = await make_adult(sessions, b)
        week_id = (await b.post("/v1/weeks")).json()["id"]
        puzzle_id = (await b.post("/v1/puzzles", {"kind": "meal"})).json()["puzzle_id"]
        async with sessions() as session, session.begin():
            job = Job(user_id=b.user["id"], kind="shiori.answer", result={"private": True})
            session.add(job)
            await session.flush()
            job_id = job.id
        await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})
        for method, path, body in (
            ("GET", f"/v1/adults/{adult_id}", None),
            ("PATCH", f"/v1/adults/{adult_id}", {"name": "renamed"}),
            ("POST", f"/v1/adults/{adult_id}/level-up", None),
            ("PUT", "/v1/team", {"adult_ids": [adult_id]}),
            ("PATCH", "/v1/me", {"favorite_adult_id": adult_id}),
            ("GET", f"/v1/jobs/{job_id}", None),
            ("GET", f"/v1/flies/{adult_id}/behavior", None),
            ("GET", f"/v1/flies/{week_id}/behavior", None),
            ("GET", f"/v1/flies/{adult_id}/brain/activity", None),
            ("POST", f"/v1/flies/{week_id}/experiments", {}),
            ("POST", f"/v1/puzzles/{puzzle_id}/submit", {"moves": [], "elapsed_ms": 0}),
            ("POST", "/v1/weeks", {"parents": [adult_id, adult_id]}),
        ):
            response = await a.client.request(
                method,
                path,
                json=body,
                headers=a.headers | {"Idempotency-Key": str(uuid4())},
            )
            assert response.status_code == 404, (method, path, response.text)
        assert (await a.get("/v1/weeks")).json() == []
        assert (await a.get("/v1/adults")).json() == []
        assert (await a.get("/v1/notifications")).json() == []
        day = (await b.get("/v1/daily-circuit")).json()["day"]
        await b.post("/v1/daily-circuit/start", {"day": day})
        assert (await a.get("/v1/daily-circuit")).json()["attempt"] is None


async def test_nonfriends_cannot_view_or_mutate_social_records(sessions: Any) -> None:
    async with GameClient(sessions, friends.router) as a, GameClient(sessions) as b:
        for method, suffix, body in (
            ("GET", "/lab", None),
            ("POST", "/like", None),
            ("POST", "/gift", {"material": "banana", "amount": 1}),
            ("DELETE", "", None),
        ):
            response = await a.client.request(
                method,
                f"/v1/friends/{b.user['id']}{suffix}",
                json=body,
                headers=a.headers | {"Idempotency-Key": str(uuid4())},
            )
            assert response.status_code == 404
