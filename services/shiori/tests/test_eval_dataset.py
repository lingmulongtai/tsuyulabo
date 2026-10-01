from __future__ import annotations

import json

import pytest
from tsuyu_shiori.dataset.export import export_dataset
from tsuyu_shiori.dataset.questions import questions
from tsuyu_shiori.dataset.traces import oracle_trace, replay
from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.eval_dataset import evaluate_file, expected_facts, grade_answer
from tsuyu_shiori.gateway import MockProvider, Response, ToolCall


@pytest.mark.asyncio
async def test_heldout_grades_native_facts_and_rejects_altered_data(tmp_path):
    await export_dataset(tmp_path, 1, 1)
    path = tmp_path / "test.jsonl"
    report = await evaluate_file(MockProvider(), path, limit=2)
    assert report["accuracy"] == 1 and report["questions"] == 2
    rows = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()]

    class OracleProvider(MockProvider):
        async def complete(self, messages, tools, model):
            request = next(m["content"] for m in messages if m["role"] == "user")
            example = next(row for row in rows if row["messages"][1]["content"] == request)
            rounds = sum(m["role"] == "assistant" for m in messages)
            message = [m for m in example["messages"] if m["role"] == "assistant"][rounds]
            return Response(
                text=message["content"],
                tool_calls=[
                    ToolCall(c["id"], c["function"]["name"], c["function"]["arguments"])
                    for c in message.get("tool_calls", [])
                ],
            )

    oracle = await evaluate_file(OracleProvider(), path)
    assert oracle["passed"] and oracle["accuracy"] == 1
    assert oracle["verification_rate"] == 1 and oracle["fallback_count"] == 0
    rows[0]["messages"][-1]["content"] = "wrong"
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        await evaluate_file(MockProvider(), path, limit=1)


@pytest.mark.asyncio
async def test_grade_rejects_wrong_counts_cause_and_negated_ai_identity():
    for intent in ("success", "why", "injection"):
        q = next(q for q in questions(2) if q.intent == intent)
        example = await oracle_trace(37, q)
        facts = expected_facts(q, await replay(example, build_world(37)))
        answer = example["messages"][-1]["content"]
        assert grade_answer(answer, q, facts)
        if intent == "success":
            wrong = answer.replace("1回", "99回")
        elif intent == "why":
            wrong = answer.replace("20回", "999回")
            assert not grade_answer(
                answer.replace("原因の断定はできません", "原因は証明済み"), q, facts
            )
        else:
            wrong = answer.replace("私はAIで、", "私はAIではありませんが、")
        assert not grade_answer(wrong, q, facts)
