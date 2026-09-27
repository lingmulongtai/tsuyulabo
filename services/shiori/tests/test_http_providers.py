from __future__ import annotations

import json

import httpx
import pytest
from tsuyu_shiori.gateway.http import AnthropicProvider, OpenAIProvider


@pytest.mark.parametrize("vendor", ["openai", "anthropic"])
async def test_wire_tools_continuation_and_cost(vendor: str) -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if vendor == "openai":
            assert request.url.path == "/v1/responses"
            assert body["tools"][0]["parameters"]["type"] == "object"
            output = [
                {
                    "type": "function_call",
                    "call_id": "t1",
                    "name": "get_care_events",
                    "arguments": '{"week_id":"w"}',
                }
            ]
            return httpx.Response(
                200, json={"output": output, "usage": {"input_tokens": 100, "output_tokens": 10}}
            )
        assert request.url.path == "/v1/messages"
        assert body["tools"][0]["input_schema"]["type"] == "object"
        return httpx.Response(
            200,
            json={
                "content": [
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "get_care_events",
                        "input": {"week_id": "w"},
                    }
                ],
                "usage": {"input_tokens": 100, "output_tokens": 10},
            },
        )

    cls = OpenAIProvider if vendor == "openai" else AnthropicProvider
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = cls(api_key="test", client=client, rates=(1, 2))
        messages = [{"role": "system", "content": "promises"}, {"role": "user", "content": "q"}]
        tools = [
            {"name": "get_care_events", "description": "read", "parameters": {"type": "object"}}
        ]
        result = await provider.complete(messages, tools, provider.model_for("qa"))
        assert result.tool_calls[0].arguments == {"week_id": "w"}
        assert result.cost.usd == pytest.approx(0.00012)
        messages.extend(
            [
                {"role": "assistant", "content": "", "continuation": result.continuation},
                {"role": "tool", "call_id": "t1", "content": "[]"},
            ]
        )
        await provider.complete(messages, tools, provider.model_for("journal"))
        assert requests[0]["model"] != requests[1]["model"]
        if vendor == "openai":
            assert requests[1]["input"][-1]["type"] == "function_call_output"
        else:
            assert requests[1]["messages"][-1]["content"][0]["tool_use_id"] == "t1"


async def test_http_errors_propagate_without_caching() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(429, json={"error": "limited"}))
    ) as client:
        provider = OpenAIProvider(api_key="test", client=client)
        with pytest.raises(httpx.HTTPStatusError):
            await provider.complete([], [], "model")
