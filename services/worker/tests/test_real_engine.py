from __future__ import annotations

from typing import Any

import pytest
from tsuyu_shiori.gateway import MockProvider
from tsuyu_worker.jobs import brain_run_experiment, shiori_answer
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, Job, LarvaState
from tsuyulabo_api.services.brain_state import store


@pytest.mark.parametrize("fly_id", ["w", "f"])
async def test_jobs_use_real_stored_adult_and_larval_states(sessions: Any, fly_id: str) -> None:
    brain = BrainAdapter()
    learned = brain.new()
    for seed in range(3):
        learned, _ = brain.train(learned, "banana", "reward", 1, seed)
    async with sessions() as session, session.begin():
        if fly_id == "w":
            row = LarvaState(week_id="w")
            session.add(row)
        else:
            row = await session.get(Adult, "f")
            learned, _ = brain.eclose(learned, [], "f", 42)
        store(row, learned, brain)
        before = row.learned_weights
        session.add_all(
            [
                Job(id="real-exp", user_id="u", kind="brain_run_experiment"),
                Job(id="real-answer", user_id="u", kind="shiori_answer"),
            ]
        )
    result = await brain_run_experiment(
        "real-exp", sessions=sessions, params={"fly_id": fly_id, "cue": "banana", "seed": 4}
    )
    assert result["result"]["toward"] > result["result"]["away"]
    answer = await shiori_answer(
        "real-answer",
        sessions=sessions,
        params={"fly_id": fly_id, "question": "bananaの好みを実験して"},
        provider=MockProvider(),
    )
    assert answer["answer"] and answer["experiments"]
    async with sessions() as session:
        row = await session.get(LarvaState if fly_id == "w" else Adult, fly_id)
        assert row.learned_weights == before
        assert (await session.get(Job, "real-answer")).status == "succeeded"
