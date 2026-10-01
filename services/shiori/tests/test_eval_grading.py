from __future__ import annotations

import pytest
from tsuyu_shiori.eval_grading import (
    APPROACH,
    SUCCESS,
    TRIALS,
    citation,
    count_answer,
    has_facts,
    number,
)


@pytest.mark.parametrize(
    "text", ["該当する記録は3回です。", "報酬を３ 回覚えました。", "3回 #0412。"]
)
def test_counts_do_not_depend_on_mock_phrase(text: str) -> None:
    assert count_answer(text) == 3


def test_ambiguous_counts_and_numeric_boundaries() -> None:
    assert count_answer("報酬3回、罰2回。") is None
    assert count_answer("不明 #0003。") is None
    assert has_facts("20 回のコピー実験では15回近づきました。", [TRIALS, APPROACH])
    assert has_facts("好みの値は0.47でした。", [number("0.47")])
    assert not has_facts("スコア180", [number("80")])
    assert not has_facts("接近115回", [APPROACH])
    assert not has_facts("値は−0.47", [number("0.47")])
    assert has_facts("値は+0.47", [number("0.47")])
    assert count_answer("-1回 #0412。") is None
    assert has_facts("結果 #9003。", [citation("#9003")])
    assert not has_facts("結果 #90030。", [citation("#9003")])
    assert has_facts("大成功の記録は1回です #9002。", [SUCCESS])
    assert not has_facts("大成功の記録 #9002。報酬1回 #9001。", [SUCCESS])


def test_equivalent_decimal_facts_accept_trailing_zeros() -> None:
    assert has_facts("値は-0.40です。", [number("-0.4")])
    assert has_facts("スコア80.0です。", [number("80")])
    assert not has_facts("値は-0.41です。", [number("-0.4")])
