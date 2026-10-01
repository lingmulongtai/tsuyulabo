from __future__ import annotations

import pytest
from tsuyu_shiori.agent import run_agent
from tsuyu_shiori.gateway import MockProvider, Response, ToolCall
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.tools import ToolContext


def context() -> ToolContext:
    store = MemoryRecordStore(
        [Record("#0001", "training", {"cue": "banana", "value": 0.4}, "w", "f")]
    )
    return ToolContext(store, MemoryLab(store, {"f": {"banana": 0.4}}), "w", "f")


async def test_mock_uses_tools_and_verifies_result() -> None:
    result = await run_agent("なんでバナナに近づくの？", context(), provider=MockProvider())
    assert result.steps == 2
    assert "接近14回" in result.text
    assert "#c-1" in result.evidence_ids
    assert result.verification.rate == 1
    assert result.cost["usd"] == 0
    assert len(result.cost["calls"]) == 2


async def test_loop_limit_and_duplicate_experiments() -> None:
    class Endless(MockProvider):
        calls = 0

        async def complete(self, messages: list, tools: list, model: str) -> Response:
            self.calls += 1
            if self.calls == 4:
                assert tools == []
            return Response(
                tool_calls=[
                    ToolCall(str(self.calls), "run_odor_choice", {"fly_id": "f", "cue": "banana"})
                ]
            )

    provider = Endless()
    result = await run_agent("実験", context(), provider=provider)
    assert provider.calls == 4
    assert result.experiments == ["#c-1"]
    assert result.stopped_reason == "fallback"
    assert result.fallback_used and result.text
    with pytest.raises(ValueError):
        await run_agent("x", context(), max_steps=5)


async def test_final_is_filtered_even_with_real_but_unseen_ids() -> None:
    class Unsupported(MockProvider):
        async def complete(self, messages: list, tools: list, model: str) -> Response:
            return Response("実在するけど未取得 #0001。捏造 #9999。")

    result = await run_agent("記録", context(), provider=Unsupported())
    assert result.provider_verification.dropped == 2
    assert result.provider_text == ""
    assert result.evidence_ids == ["#0001"]
    assert result.fallback_used and result.text


async def test_empty_store_returns_status_without_invented_citations() -> None:
    store = MemoryRecordStore()
    result = await run_agent(
        "ごはんの結果は？",
        ToolContext(store, MemoryLab(store, {}), "w", "f"),
        provider=MockProvider(),
    )
    assert result.text and result.empty_state and result.fallback_used
    assert result.evidence_ids == [] and result.verification.kept == 0


async def test_uncited_answer_is_retried_before_acceptance() -> None:
    class Premature(MockProvider):
        attempts = 0

        async def complete(self, messages: list, tools: list, model: str) -> Response:
            self.attempts += 1
            if self.attempts == 1:
                return Response("0回です #0001。")
            return await super().complete(messages, tools, model)

    provider = Premature()
    result = await run_agent("バナナのしつけは何回？", context(), provider=provider)
    assert not result.fallback_used
    assert result.steps == 3 and "1回" in result.text


async def test_fallback_reuses_experiments_and_feature_limit() -> None:
    class InvalidFinal(MockProvider):
        async def complete(self, messages: list, tools: list, model: str) -> Response:
            response = await super().complete(messages, tools, model)
            return Response("引用なし。") if response.text else response

    ctx = context()
    result = await run_agent(
        "バナナの好みは？",
        ctx,
        provider=InvalidFinal(),
        max_sentences=1,
    )
    assert result.fallback_used and result.text.count("。") == 1
    assert result.experiments == ["#c-1"]
    assert result.provider_verification.dropped == 1
    assert result.to_dict()["fallback_used"] is True
