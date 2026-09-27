from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from tsuyulabo_api.db.models import Job
from tsuyulabo_api.routers import jobs
from tsuyulabo_api.services.dispatch import enqueue
from tsuyulabo_api.services.game import CurrentUser, Session
from tsuyulabo_api.services.idempotency import IdempotentRoute

from .game_support import GameClient


async def test_dispatch_runs_after_commit_and_preserves_inputs_on_failure(sessions: Any) -> None:
    router = APIRouter(route_class=IdempotentRoute)

    @router.post("/enqueue")
    async def route(
        request: Request, tasks: BackgroundTasks, user: CurrentUser, session: Session
    ) -> dict:
        job = await enqueue(session, request, tasks, user.id, "test", {"value": 42})
        return {"job_id": job.id}

    class Queue:
        async def enqueue(self, job_id: str, kind: str, params: dict) -> None:
            async with sessions() as session:
                job = await session.get(Job, job_id)
                assert job.params == params == {"value": 42}
            raise RuntimeError("queue unavailable")

    async with GameClient(sessions, router, jobs.router) as game:
        game.app.state.job_queue = Queue()
        response = await game.post("/enqueue")
        job = (await game.get(f"/v1/jobs/{response.json()['job_id']}")).json()
        assert job["status"] == "failed" and job["error"]["code"] == "enqueue_failed"
