from __future__ import annotations

import pytest
from tsuyu_shiori.dataset.counts import count_answer, count_calls
from tsuyu_shiori.dataset.questions import questions
from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.eval import readability
from tsuyu_shiori.tools import execute
from tsuyu_shiori.verify import verify


@pytest.mark.asyncio
async def test_exact_counts_and_weekdays():
    context = build_world(1000)
    for q in questions():
        if not q.intent.startswith("count") and q.intent != "maximum":
            continue
        results = [await execute(context, name, args) for name, args in count_calls(q, "eval-week")]
        for result in results:
            filters = result["filters"]
            expected = sum(
                r.kind == "training"
                and all(
                    filters[key] is None or r.data.get(key) == filters[key]
                    for key in ("cue", "valence", "research_day")
                )
                for r in context.store.records.values()
            )
            assert result["count"] == expected
        for pattern in range(3):
            answer = count_answer(q, results, pattern)
            checked = await verify(
                answer, context.store, allowed_ids={i for r in results for i in r["ids"]}
            )
            assert checked.report.dropped == 0
            assert readability(answer)["passed"]
