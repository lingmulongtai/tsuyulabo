from __future__ import annotations

import json

from tsuyu_shiori.dataset.companion import INTENTS, companion_questions, companion_trace
from tsuyu_shiori.dataset.export import export_dataset
from tsuyu_shiori.dataset.world import build_world


async def test_v3_traces_include_cited_companion_intents_and_new_persona(tmp_path):
    for intent in INTENTS:
        q = next(q for q in companion_questions(2) if q.intent == intent)
        example = await companion_trace(37, q)
        assert example == await companion_trace(37, q)
        assert "飼育を手伝う相棒" in example["messages"][0]["content"]
        assert example["messages"][-1]["content"].count("。") in {1, 2, 3}
        assert "#" in example["messages"][-1]["content"]
    stats = await export_dataset(tmp_path, 100, 100, balanced=True, companion=True)
    assert stats["version"] == 3
    assert set(stats["splits"]["train"]["intents"]) >= INTENTS
    assert stats["splits"]["test"]["examples"] == 163
    assert not set(stats["splits"]["train"]["seeds"]) & set(stats["splits"]["valid"]["seeds"])
    assert all(
        set(json.loads(row)) == {"messages", "tools"}
        for row in (tmp_path / "train.jsonl").read_text(encoding="utf-8").splitlines()
    )


async def test_unmeasured_cues_do_not_become_associations_in_training_world():
    for seed in (37, 1000, 1001):
        context = build_world(seed)
        assert await context.store.association(context.fly_id, "yeast") is None
        assert await context.store.association(context.fly_id, "blue_light") is None
