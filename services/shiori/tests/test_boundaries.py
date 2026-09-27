from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx
import pytest
from tsuyu_shiori.agent import run_agent
from tsuyu_shiori.gateway import AnthropicProvider, MockProvider, OpenAIProvider, Response, ToolCall
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.tools import ToolContext


async def test_fanout_limit() -> None:
    class ManyCalls(MockProvider):
        calls = 0

        async def complete(self, messages: list, tools: list, model: str) -> Response:
            self.calls += 1
            if self.calls == 1:
                return Response(
                    tool_calls=[
                        ToolCall(
                            str(i),
                            "run_odor_choice",
                            {
                                "fly_id": "f",
                                "cue": "banana",
                                "seed": i,
                            },
                        )
                        for i in range(6)
                    ]
                )
            outputs = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
            assert len(outputs) == 6
            assert [r["error"] for r in outputs[-2:]] == ["tool_call_limit"] * 2
            return Response("コピーの結果です #c-1。")

    store = MemoryRecordStore()
    result = await run_agent(
        "実験", ToolContext(store, MemoryLab(store, {"f": {}}), "w", "f"), provider=ManyCalls()
    )
    assert len(result.experiments) == 4
    assert result.verification.rate == 1


async def test_paper_citations_come_from_retrieval() -> None:
    store = MemoryRecordStore([Record("#0001", "meal", {}, "w")])
    answer = await run_agent(
        "MN9 の論文を教えて",
        ToolContext(store, MemoryLab(store, {}), "w", "f"),
        provider=MockProvider(),
    )
    assert any(evidence.startswith("#p-") for evidence in answer.evidence_ids)
    assert answer.verification.rate == 1


@pytest.mark.parametrize("vendor", ["openai", "anthropic"])
async def test_http_final_text_and_authentication(vendor: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if vendor == "openai":
            assert request.headers["authorization"] == "Bearer test-key"
            return httpx.Response(
                200,
                json={
                    "output": [
                        {
                            "type": "message",
                            "content": [{"type": "output_text", "text": "結果 #0001。"}],
                        }
                    ],
                    "usage": {"input_tokens": 6, "output_tokens": 4},
                },
            )
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "結果 #0001。"}],
                "usage": {"input_tokens": 6, "output_tokens": 4},
            },
        )

    cls = OpenAIProvider if vendor == "openai" else AnthropicProvider
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await cls(api_key="test-key", client=client).complete([], [], "test-model")
    assert result.text == "結果 #0001。" and not result.tool_calls
    assert result.cost.input_tokens == 6 and result.cost.output_tokens == 4


async def test_weekday_questions_use_jst_even_when_records_are_utc() -> None:
    # Monday in UTC, Tuesday in the game timezone.
    store = MemoryRecordStore(
        [
            Record(
                "#0001",
                "training",
                {
                    "cue": "apple_vinegar",
                    "valence": "punish",
                },
                "w",
                occurred_at=datetime(2026, 9, 21, 16, tzinfo=UTC),
            )
        ]
    )
    answer = await run_agent(
        "火曜にりんご酢で罰を何回覚えた？",
        ToolContext(store, MemoryLab(store, {}), "w", "f"),
        provider=MockProvider(),
    )
    assert "1回" in answer.text
