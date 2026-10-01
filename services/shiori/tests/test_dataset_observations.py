from __future__ import annotations

from copy import deepcopy

import pytest
from tsuyu_shiori.dataset.observations import observation_answer, observation_calls
from tsuyu_shiori.dataset.questions import questions
from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.eval import readability
from tsuyu_shiori.tools import execute
from tsuyu_shiori.verify import verify


@pytest.mark.asyncio
async def test_observations_experiments_research_and_refusals():
    for seed in (37, 1000, 1001):
        for q in questions(2):
            if q.intent.startswith("count") or q.intent == "maximum":
                continue
            context = build_world(seed)
            states = deepcopy(context.lab.states)
            results = [
                await execute(context, name, args)
                for name, args in observation_calls(q, "eval-week", "eval-fly")
            ]
            assert context.lab.states == states
            papers = {p["id"] for r in results for p in r.get("papers", [])}
            allowed = papers | {
                x["id"] for r in results for x in r.get("records", []) + r.get("sleep_sessions", [])
            }
            allowed |= {i for r in results for i in r.get("ids", [])}
            variations = set()
            for pattern in range(3):
                answer = observation_answer(q, results, pattern)
                variations.add(answer)
                checked = await verify(answer, context.store, allowed_ids=allowed, paper_ids=papers)
                assert checked.report.dropped == 0, answer
                assert readability(answer)["passed"], answer
            assert len(variations) == 3, q.intent
            if q.intent == "injection":
                assert "私はAI" in answer and "本物を変更しません" in answer
