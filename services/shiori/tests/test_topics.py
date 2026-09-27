from __future__ import annotations

import pytest
from tsuyu_shiori.gateway.topics import citations, compact, newest, observations, topic_in
from tsuyu_shiori.verify import ID_PATTERN, split_sentences


@pytest.mark.parametrize(
    ("question", "topic"),
    [
        ("しつけで脳はどう変わる？", "training"),
        ("りんご酢は？", "training"),
        ("寝た時間は？", "sleep"),
        ("掃除の結果", "cleaning"),
        ("温度は？", "temperature"),
        ("大成功した？", "meal"),
        ("羽化した特性は？", "eclosion"),
    ],
)
def test_topics(question: str, topic: str) -> None:
    assert topic_in(question) == topic


def test_recent_relevant_records_and_short_answer() -> None:
    records = [
        {
            "id": f"#{i:04}",
            "kind": "training",
            "data": {"cue": "banana", "value": i / 100, "valence": "reward"},
        }
        for i in range(1, 47)
    ]
    records.append({"id": "#9999", "kind": "meal", "data": {}})
    answer = compact(observations("バナナのしつけ", records, [], records))
    assert "46回" in answer and "+0.46" in answer
    assert "#0046" in answer and "#0001" not in answer and "#9999" not in answer
    assert len(answer) <= 160
    assert len(ID_PATTERN.findall(answer)) <= 6
    assert all(1 <= len(ID_PATTERN.findall(s)) <= 4 for s in split_sentences(answer))


def test_recency_uses_instants_and_sequence_tiebreak() -> None:
    records = [
        {"id": "#0001", "occurred_at": "2026-09-22T00:00:00+09:00"},
        {"id": "#0002", "occurred_at": "2026-09-21T16:00:00+00:00"},
    ]
    assert newest(records)[0]["id"] == "#0002"
    assert citations([{"id": f"#{i:04}"} for i in range(10)]) == "#0009 #0008 #0007"


def test_missing_topic_is_explicit_and_does_not_invent_measurements() -> None:
    care = [{"id": "#0001", "kind": "meal", "data": {}}]
    answer = compact(observations("温度は？", care, [], care))
    assert "該当記録がありません" in answer and "記録を残して" in answer
    assert observations("睡眠は？", [], [], []) == []


def test_compact_counts_repeated_ids_and_preserves_whole_sentences() -> None:
    assert compact(["長" * 160 + " #0001。", "観察 #0002。"]) == "観察 #0002。"
    answer = compact(["観察 #0001 #0002 #0003。"] * 3)
    assert len(ID_PATTERN.findall(answer)) == 6
