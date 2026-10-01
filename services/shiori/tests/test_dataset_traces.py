from __future__ import annotations

import json
from copy import deepcopy

import pytest
from tsuyu_shiori.dataset.questions import questions
from tsuyu_shiori.dataset.traces import oracle_trace, replay
from tsuyu_shiori.dataset.world import build_world


@pytest.mark.asyncio
async def test_all_intents_templates_replay_and_are_deterministic():
    for seed in (37, 1000):
        for variant in range(3):
            for q in questions(variant):
                example = await oracle_trace(seed, q)
                if variant == 0 and q.intent == "why":
                    assert example == await oracle_trace(seed, q)
                assert json.loads(json.dumps(example)) == example
                await replay(example, build_world(seed))
    bad = deepcopy(example)
    next(m for m in bad["messages"] if m["role"] == "tool")["content"] = "{}"
    with pytest.raises(ValueError, match="replay differs"):
        await replay(bad, build_world(seed))
