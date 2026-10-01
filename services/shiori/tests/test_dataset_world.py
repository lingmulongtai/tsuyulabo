from __future__ import annotations

from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.eval import open_questions, synthesize, topic_questions


def test_eval_world_and_seed_variation():
    expected, _ = synthesize(37)
    topic_questions(expected)
    open_questions(expected)
    assert build_world(37).store.records == expected.records
    a, b = build_world(1000), build_world(1001)
    assert a.store.records == build_world(1000).store.records
    assert a.store.records != b.store.records
    assert a.lab.states != b.lab.states
