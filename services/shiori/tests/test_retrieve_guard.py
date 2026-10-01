from __future__ import annotations

import pytest
from tsuyu_shiori.agent import run_agent
from tsuyu_shiori.gateway import MockProvider, Response, ToolCall
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.tools import ToolContext


@pytest.mark.parametrize("tool", ["get_association", "run_odor_choice"])
async def test_any_successful_record_tool_allows_answer(tool: str) -> None:
    class Provider(MockProvider):
        calls = 0

        async def complete(self, messages: list, tools: list, model: str) -> Response:
            self.calls += 1
            if self.calls == 1:
                args = (
                    {"week_id": "w"}
                    if tool == "count_care_events"
                    else {"fly_id": "f", "cue": "banana"}
                )
                return Response(tool_calls=[ToolCall("record", tool, args)])
            return Response(
                "確認した結果です #0001。"
                if tool != "run_odor_choice"
                else "コピーの結果です #c-1。"
            )

    store = MemoryRecordStore(
        [Record("#0001", "training", {"cue": "banana", "value": 0.4}, "w", "f")]
    )
    provider = Provider()
    answer = await run_agent(
        "結果は？", ToolContext(store, MemoryLab(store, {"f": {}}), "w", "f"), provider=provider
    )
    assert provider.calls == 2 and not answer.fallback_used


async def test_papers_alone_do_not_satisfy_record_guard() -> None:
    class Provider(MockProvider):
        calls = 0

        async def complete(self, messages: list, tools: list, model: str) -> Response:
            self.calls += 1
            if self.calls == 1:
                return Response(tool_calls=[ToolCall("paper", "search_papers", {"query": "脳"})])
            if self.calls == 2:
                return Response("説明です。")
            if self.calls == 3:
                assert "記録未取得" in messages[-1]["content"]
            return await super().complete(messages, tools, model)

    store = MemoryRecordStore()
    await run_agent(
        "脳は？", ToolContext(store, MemoryLab(store, {}), "w", "f"), provider=Provider()
    )
