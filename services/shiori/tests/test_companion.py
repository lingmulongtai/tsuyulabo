from __future__ import annotations

from tsuyu_shiori.companion import diary_entry, intent_provider, quiet_hint
from tsuyu_shiori.diary_events import Moment
from tsuyu_shiori.gateway import MockProvider
from tsuyu_shiori.hint_rules import Trouble
from tsuyu_shiori.records import MemoryRecordStore, Record
from tsuyu_shiori.verify import split_sentences


async def test_new_intents_are_cited_short_and_do_not_invent_state():
    store = MemoryRecordStore([Record("#0001", "meal", {}, "w")])
    diary = await diary_entry([Moment("meal", "ごはんを入れました", ["#0001"], {})], store)
    assert len(split_sentences(diary.text)) == 2
    assert "ごはんを入れました" in diary.text
    assert diary.evidence_ids == ["#0001"]
    hint = await quiet_hint(
        Trouble("dry", "餌が乾いています", "ごはんを用意しましょう"), "#0001", store
    )
    assert len(split_sentences(hint.text)) == 1
    assert "乾いて" in hint.text and "ごはん" in hint.text
    assert hint.verification.rate == 1


def test_intent_acceptance_does_not_switch_existing_qa(monkeypatch):
    candidate = object()
    monkeypatch.delenv("SHIORI_ACCEPTED_INTENTS", raising=False)
    assert isinstance(intent_provider("diary", candidate), MockProvider)
    monkeypatch.setenv("SHIORI_ACCEPTED_INTENTS", "diary")
    assert intent_provider("diary", candidate) is candidate
    assert isinstance(intent_provider("hint", candidate), MockProvider)


async def test_mock_v3_weaknesses_use_cue_names_identity_and_missing_facts():
    from tsuyu_shiori.dataset.questions import questions
    from tsuyu_shiori.dataset.traces import oracle_trace, replay
    from tsuyu_shiori.dataset.world import build_world
    from tsuyu_shiori.eval_dataset import expected_facts, grade_answer
    from tsuyu_shiori.features import answer_question

    for intent in ("maximum", "injection", "missing"):
        q = next(q for q in questions(2) if q.intent == intent)
        example = await oracle_trace(37, q)
        facts = expected_facts(q, await replay(example, build_world(37)))
        context = build_world(37)
        answer = await answer_question(
            q.text,
            store=context.store,
            lab=context.lab,
            week_id=context.week_id,
            fly_id=context.fly_id,
            provider=MockProvider(),
        )
        assert grade_answer(answer.provider_text, q, facts), answer.text
