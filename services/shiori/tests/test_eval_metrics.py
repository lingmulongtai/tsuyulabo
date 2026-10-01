from __future__ import annotations

from tsuyu_shiori.eval_metrics import token_metrics


def test_question_tokens_sum_calls_but_context_is_per_call() -> None:
    results = [
        {"cost": {"input_tokens": 300, "calls": [{"input_tokens": 100}, {"input_tokens": 200}]}},
        {"cost": {"input_tokens": 500, "calls": [{"input_tokens": 250}, {"input_tokens": 250}]}},
    ]
    assert token_metrics(results) == {
        "input_tokens_mean_per_question": 400,
        "input_tokens_max_per_question": 500,
        "input_tokens_max_per_call": 250,
    }
    assert token_metrics([])["input_tokens_max_per_call"] == 0
