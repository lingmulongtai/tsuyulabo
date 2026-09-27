from __future__ import annotations

from typing import Any
from uuid import uuid4

from tsuyulabo_api.db.models import Job, ShioriMessage
from tsuyulabo_api.routers import jobs, shiori

from .game_support import GameClient


async def test_memo_and_question_job_plumbing(sessions: Any) -> None:
    calls = []

    class Queue:
        async def enqueue(self, job_id: str, kind: str, params: dict) -> None:
            async with sessions() as session:
                assert (await session.get(Job, job_id)).kind == "shiori.answer"
            calls.append((kind, params))

    async with GameClient(sessions, shiori.router, jobs.router) as game:
        game.app.state.job_queue = Queue()
        assert (await game.get("/v1/shiori/memo")).json() is None
        async with sessions() as session, session.begin():
            session.add(
                ShioriMessage(
                    user_id=game.user["id"],
                    role="memo",
                    text="memo",
                    evidence=["#0001"],
                    created_at=game.clock.now(),
                )
            )
        assert (await game.get("/v1/shiori/memo")).json()["text"] == "memo"
        key = str(uuid4())
        response = await game.post("/v1/shiori/ask", {"question": "why?"}, key)
        assert response.status_code == 202
        assert (
            await game.post("/v1/shiori/ask", {"question": "why?"}, key)
        ).json() == response.json()
        assert len(calls) == 1 and calls[0][0] == "shiori.answer"
        job_id = response.json()["job_id"]
        assert (await game.get(f"/v1/jobs/{job_id}")).json()["status"] == "pending"
        assert (await game.post("/v1/shiori/ask", {"question": "   "})).status_code == 422
        async with GameClient(sessions, jobs.router) as other:
            assert (await other.get(f"/v1/jobs/{job_id}")).status_code == 404
