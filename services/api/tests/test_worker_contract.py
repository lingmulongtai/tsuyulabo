from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from sqlalchemy import func, select
from tsuyu_shiori.gateway import MockProvider
from tsuyu_worker.main import run_brain_job
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Experiment, Job, LarvaState
from tsuyulabo_api.routers import brain, jobs, puzzles, shiori, weeks
from tsuyulabo_api.services import deferred
from tsuyulabo_api.services.jobs import ArqJobQueue

from .game_support import GameClient
from .test_queued_training import issue_training


async def test_worker_accepts_exact_api_arq_payloads(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple] = []

    class Pool:
        async def enqueue_job(self, function: str, *args: Any, **kwargs: Any) -> None:
            assert function == "run_brain_job" and kwargs == {"_job_id": args[0]}
            calls.append(tuple(json.loads(json.dumps(args))))

    queue = ArqJobQueue("redis://unused")
    queue.pool = Pool()
    monkeypatch.setattr(deferred, "LEARNING_WAIT_SECONDS", 0.01)
    async with GameClient(
        sessions, weeks.router, puzzles.router, brain.router, shiori.router, jobs.router
    ) as game:
        game.app.state.brain_adapter = BrainAdapter()
        game.app.state.settings.brain_mode = "queue"
        game.app.state.job_queue = queue
        week_id = (await game.post("/v1/weeks")).json()["id"]
        await game.advance(to="next_day")
        path, body = await issue_training(game, sessions)
        pending = (await game.post(path, body)).json()
        assert pending["learning_status"] == "pending"
        ctx = {"sessions": sessions, "provider": MockProvider()}
        training_call = calls[-1]
        assert training_call[1] == "brain.training"
        learned = await run_brain_job(ctx, *training_call)
        assert learned["learning_status"] == "completed", learned
        assert await run_brain_job(ctx, *training_call) == learned
        await asyncio.gather(*game.app.state.pending_calculations)

        for path, body, kind in [
            (
                f"/v1/flies/{week_id}/experiments",
                {"cue": "banana", "trials": 20},
                "brain.experiment",
            ),
            ("/v1/shiori/ask", {"question": "bananaの好みを実験して"}, "shiori.answer"),
        ]:
            response = await game.post(path, body)
            assert response.status_code == 202, response.text
            call = calls[-1]
            assert call[1] == kind
            result = await run_brain_job(ctx, *call)
            assert "error" not in result, result
            assert await run_brain_job(ctx, *call) == result
            polled = (await game.get(f"/v1/jobs/{call[0]}")).json()
            assert polled["status"] == "succeeded" and polled["result"] == result
            if kind == "shiori.answer":
                assert result["answer"] and result["experiments"]
        async with sessions() as session:
            larva = await session.get(LarvaState, week_id)
            assert len(larva.brain_snapshot["training"]) == 1
            assert larva.preferences["banana"] > 0
            assert await session.scalar(select(func.count()).select_from(Experiment)) == 2
            assert all(job.status == "succeeded" for job in await session.scalars(select(Job)))
