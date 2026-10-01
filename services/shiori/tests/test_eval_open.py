from __future__ import annotations

from tsuyu_shiori.eval import synthesize, topic_questions
from tsuyu_shiori.eval_grading import has_facts
from tsuyu_shiori.eval_open import open_questions
from tsuyu_shiori.features import answer_question
from tsuyu_shiori.gateway import MockProvider
from tsuyu_shiori.records import MemoryLab


async def test_mock_answers_all_open_questions_with_facts() -> None:
    store, _ = synthesize()
    topic_questions(store)
    questions = open_questions(store)
    assert len(questions) == 10
    for question, facts in questions:
        answer = await answer_question(
            question,
            store=store,
            lab=MemoryLab(store, {"eval-fly": {"banana": 0.47, "apple_vinegar": -0.4}}),
            week_id="eval-week",
            fly_id="eval-fly",
            provider=MockProvider(),
        )
        assert has_facts(answer.provider_text, facts), (question, answer.text)
        assert not answer.fallback_used
        assert answer.verification.rate == 1


def test_open_grading_accepts_paraphrased_facts() -> None:
    store, _ = synthesize()
    topic_questions(store)
    questions = dict(open_questions(store))
    assert has_facts("結果はにじランクでした #9006。", questions["発表会のランクは？"])
    assert has_facts("#s-7 の計測値は7.7時間でした。", questions["最近よく眠れてる？"])
    assert not has_facts("8時間ぐっすりでした #s-7。", questions["最近よく眠れてる？"])
