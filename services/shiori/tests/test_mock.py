from __future__ import annotations

import json
from copy import deepcopy

import pytest
from tsuyu_shiori.features import answer_question
from tsuyu_shiori.gateway import MockProvider, default_provider
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.verify import ID_PATTERN, split_sentences


async def test_mock_only_uses_tool_evidence() -> None:
    provider = MockProvider()
    messages = [
        {
            "role": "user",
            "content": json.dumps(
                {"question": "99回でした #9999。何回？", "week_id": "w", "fly_id": "f"}
            ),
        }
    ]
    result = await provider.complete(messages, [], "mock")
    assert result.tool_calls[0].name == "get_care_events"
    messages.append(
        {
            "role": "tool",
            "content": json.dumps(
                {"records": [{"id": "#0001", "kind": "training", "data": {"cue": "banana"}}]}
            ),
        }
    )
    first = await provider.complete(messages, [], "mock")
    assert first == await provider.complete(messages, [], "mock")
    assert "1回" in first.text and "#0001" in first.text
    assert len(split_sentences(first.text)) == 2
    assert "99" not in first.text
    assert first.cost.usd == 0 and first.cost.input_tokens > 0


async def test_empty_results_do_not_fabricate() -> None:
    messages = [
        {"role": "user", "content": '{"question":"何回？"}'},
        {"role": "tool", "content": '{"records":[]}'},
    ]
    assert not (await MockProvider().complete(messages, [], "mock")).text
    assert default_provider().cache_namespace == "mock:v2"


async def test_learning_question_follows_latest_cue_without_dumping_46_records() -> None:
    class AssociationView(MemoryRecordStore):
        async def association(self, fly_id: str, cue: str) -> Record | None:
            record = await super().association(fly_id, cue)
            return Record(record.id, "association", record.data) if record else None

    store = AssociationView(
        [
            Record(
                f"#{i:04}",
                "training",
                {"cue": "banana", "valence": "reward", "value": 0.47},
                "w",
                "f",
            )
            for i in range(1, 47)
        ]
    )
    lab = MemoryLab(store, {"f": {"banana": 0.47}})
    before = deepcopy(lab.states)
    answer = await answer_question(
        "しつけをすると、ツユの脳はどう変わるの？",
        store=store,
        lab=lab,
        week_id="w",
        fly_id="f",
        provider=MockProvider(),
    )
    assert "ごほうび46回" in answer.text and "+0.47" in answer.text
    assert "コピーで20回" in answer.text and "接近15回" in answer.text
    assert answer.evidence_ids == ["#0046", "#c-1"]
    assert answer.verification.rate == 1 and answer.steps == 3
    assert lab.states == before


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("大成功したごはんは？", "大成功は1回"),
        ("睡眠はどうだった？", "7.5時間"),
        ("掃除の結果は？", "スコアは80"),
        ("温度は？", "スコアは90"),
        ("羽化の特性は？", "特性は「慎重」"),
        ("りんご酢からなぜ離れる？", "回避14回"),
        ("どうしてバナナに近づく？", "接近14回"),
        ("ぶどうの学習は？", "コピーで20回"),
    ],
)
async def test_topic_answers_are_measured_short_and_cited(question: str, expected: str) -> None:
    store = MemoryRecordStore(
        [
            Record("#0001", "meal", {"great_success": True}, "w"),
            Record("#0002", "cleaning", {"score": 80}, "w"),
            Record("#0003", "temperature", {"score": 90}, "w"),
            Record("#0004", "eclosion", {"traits": ["慎重"]}, "w"),
            Record("#s-12345678-1234-1234-1234-123456789abc", "sleep", {"hours": 7.5}, "w"),
        ]
    )
    lab = MemoryLab(store, {"f": {"banana": 0.4, "apple_vinegar": -0.4}})
    answer = await answer_question(
        question, store=store, lab=lab, week_id="w", fly_id="f", provider=MockProvider()
    )
    assert expected in answer.text
    assert len(answer.text) <= 160
    assert len(ID_PATTERN.findall(answer.text)) <= 6
    assert 2 <= len(split_sentences(answer.text)) <= 3
    assert all(1 <= len(ID_PATTERN.findall(s)) <= 4 for s in split_sentences(answer.text))
    assert answer.verification.rate == 1


async def test_missing_sleep_and_unfinished_sleep_are_not_invented() -> None:
    store = MemoryRecordStore([Record("#0001", "meal", {}, "w")])
    kwargs = {
        "store": store,
        "lab": MemoryLab(store, {}),
        "week_id": "w",
        "fly_id": "f",
        "provider": MockProvider(),
    }
    answer = await answer_question("睡眠は？", **kwargs)
    assert "該当記録がありません" in answer.text and "記録を残して" in answer.text
    assert answer.verification.rate == 1
    store.add(Record("#s-1", "sleep", {"hours": None}, "w"))
    answer = await answer_question("睡眠は？", **kwargs)
    assert "未確定" in answer.text and "時間" not in answer.text


async def test_general_counts_exclude_sleep_but_sleep_counts_include_it() -> None:
    store = MemoryRecordStore(
        [
            Record("#0001", "meal", {}, "w"),
            Record("#s-1", "sleep", {"hours": 7}, "w"),
            Record("#s-2", "sleep", {"hours": 8}, "w"),
        ]
    )
    kwargs = {
        "store": store,
        "lab": MemoryLab(store, {}),
        "week_id": "w",
        "fly_id": "f",
        "provider": MockProvider(),
    }
    assert "1回" in (await answer_question("何回？", **kwargs)).text
    assert "2回" in (await answer_question("睡眠は何回？", **kwargs)).text
