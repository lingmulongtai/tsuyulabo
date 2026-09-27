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
    assert result.stopped_reason == "step_limit"
    assert result.text == ""
    with pytest.raises(ValueError):
        await run_agent("x", context(), max_steps=5)


async def test_final_is_filtered_even_with_real_but_unseen_ids() -> None:
    class Unsupported(MockProvider):
        async def complete(self, messages: list, tools: list, model: str) -> Response:
            return Response("実在するけど未取得 #0001。捏造 #9999。")

    result = await run_agent("記録", context(), provider=Unsupported())
    assert result.verification.dropped == 2
    assert not result.evidence_ids
