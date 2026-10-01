from __future__ import annotations

import json
from collections import Counter

from tsuyu_shiori.dataset.export import balanced_cases, export_dataset
from tsuyu_shiori.dataset.questions import DAY_COUNTS, balanced_questions, questions


def test_balanced_world_thins_day_counts_and_doubles_rare_phrasings() -> None:
    world = balanced_questions(1000)
    intents = Counter(q.intent for q in world)
    assert sum(intents[i] for i in DAY_COUNTS) == 8
    plain = Counter(q.intent for q in questions(0))
    for intent in ("why", "preference", "research", "injection", "maximum", "success"):
        assert intents[intent] == 2 * plain[intent]
    assert {q.template_id.split(":")[1] for q in world} == {"0", "1"}
    assert balanced_questions(1000) == world
    assert [q.text for q in balanced_questions(1002)] != [q.text for q in world]


def test_balanced_cases_fill_the_size_and_keep_seed_ranges() -> None:
    cases = balanced_cases(200, 1000)
    assert len(cases) == 200
    assert min(s for s, _ in cases) == 1000 and max(s for s, _ in cases) < 2000
    share = sum(q.intent in DAY_COUNTS for _, q in cases) / len(cases)
    assert share < 0.2


async def test_balanced_export_records_the_mode(tmp_path) -> None:
    stats = await export_dataset(tmp_path, train_size=60, valid_size=10, balanced=True)
    assert stats["balanced"] is True
    assert stats["splits"]["train"]["examples"] == 60
    assert not set(stats["splits"]["train"]["seeds"]) & set(stats["splits"]["valid"]["seeds"])
    rows = (tmp_path / "train.jsonl").read_text(encoding="utf-8").splitlines()
    assert all(set(json.loads(row)) == {"messages", "tools"} for row in rows)
