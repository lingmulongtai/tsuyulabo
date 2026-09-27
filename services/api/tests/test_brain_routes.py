from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from tsuyulabo_api.db.models import Adult, Experiment
from tsuyulabo_api.routers import brain, jobs, weeks, zukan
from tsuyulabo_api.services.experiments import handler
from tsuyulabo_api.services.jobs import InlineJobQueue

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_behavior_and_inline_experiment_copy_replay_and_sequence(sessions: Any) -> None:
    async with GameClient(sessions, brain.router, jobs.router, weeks.router, zukan.router) as game:
        game.app.state.job_queue = InlineJobQueue(
            sessions, {"brain.experiment": handler(sessions, game.app.state.brain_adapter)}
        )
        adult_id = await make_adult(sessions, game)
        assert (await game.get(f"/v1/flies/{adult_id}/behavior")).json()["walk"] == 0.75
        assert (await game.get("/v1/zukan")).json()["completion"]["behaviors"] == 1 / 9
        async with sessions() as session:
            before = deepcopy((await session.get(Adult, adult_id)).brain_snapshot)
        for index in range(2):
            key = str(uuid4())
            response = await game.post(f"/v1/flies/{adult_id}/experiments", {"cue": "banana"}, key)
            assert response.status_code == 202, response.text
            assert (
                await game.post(f"/v1/flies/{adult_id}/experiments", {"cue": "banana"}, key)
            ).json() == response.json()
            job = (await game.get(f"/v1/jobs/{response.json()['job_id']}")).json()
            assert job["status"] == "succeeded", job
            assert job["result"]["display_id"] == f"c-{index + 1}"
            assert job["result"]["result"] == {"toward": 50, "away": 50}
        async with sessions() as session:
            assert len((await session.scalars(select(Experiment))).all()) == 2
            assert (await session.get(Adult, adult_id)).brain_snapshot == before
        week = (await game.post("/v1/weeks")).json()
        assert (await game.get(f"/v1/flies/{week['id']}/behavior")).status_code == 200
        assert (await game.get("/v1/flies/missing/behavior")).status_code == 404
        assert (
            await game.post(f"/v1/flies/{adult_id}/experiments", {"trials": 0})
        ).status_code == 422
        async with GameClient(sessions, brain.router) as other:
            assert (await other.get(f"/v1/flies/{adult_id}/behavior")).status_code == 404
            assert (await other.post(f"/v1/flies/{adult_id}/experiments", {})).status_code == 404
