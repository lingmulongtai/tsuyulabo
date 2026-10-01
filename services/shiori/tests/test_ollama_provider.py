from __future__ import annotations

import json

import httpx
import pytest
from tsuyu_shiori.gateway.ollama import OllamaProvider


@pytest.mark.parametrize("arguments", [{"week_id": "w"}, '{"week_id":"w"}'])
async def test_native_chat_tools_and_replay(arguments: dict | str) -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://localhost:11434/api/chat"
        body = json.loads(request.content)
        requests.append(body)
        assert body["options"] == {"num_ctx": 8192, "num_predict": 512, "temperature": 0.2}
        assert body["think"] is body["stream"] is False
        assert body["keep_alive"] == "30m"
        assert body["tools"][0]["function"]["parameters"] == {"type": "object"}
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "<think>secret\nreasoning</think>結果 #0412。",
                    "tool_calls": [
                        {"function": {"name": "get_care_events", "arguments": arguments}}
                    ],
                },
                "prompt_eval_count": 100,
                "eval_count": 12,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OllamaProvider(client=client, base_url="http://localhost:11434/")
        tools = [
            {"name": "get_care_events", "description": "read", "parameters": {"type": "object"}}
        ]
        messages = [{"role": "user", "content": "question"}]
        result = await provider.complete(messages, tools, provider.model_for("qa"))
        repeated = await provider.complete(messages, tools, provider.model_for("qa"))
        assert result.tool_calls == repeated.tool_calls
        assert result.tool_calls[0].arguments == {"week_id": "w"}
        assert result.tool_calls[0].id.startswith("call_")
        assert result.text == "結果 #0412。"
        assert result.cost.input_tokens == 100 and result.cost.output_tokens == 12
        assert result.cost.usd == 0
        messages.extend(
            [
                {"role": "assistant", "content": result.text, "continuation": result.continuation},
                {
                    "role": "tool",
                    "name": "get_care_events",
                    "call_id": result.tool_calls[0].id,
                    "content": '{"records":[]}',
                },
            ]
        )
        await provider.complete(messages, tools, provider.model_for("journal"))
        assert requests[-1]["messages"][-2] == result.continuation[0]
        assert requests[-1]["messages"][-1] == {
            "role": "tool",
            "tool_name": "get_care_events",
            "content": '{"records":[]}',
        }
        assert requests[-1]["model"] == "qwen3.5:2b-q4_K_M"


async def test_connection_error_names_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ConnectionError, match="http://localhost:11435/api/chat"):
            await OllamaProvider(client=client, base_url="http://localhost:11435").complete(
                [], [], "m"
            )


def test_environment_and_cache_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in {
        "OLLAMA_BASE_URL": "http://host:11435",
        "OLLAMA_QA_MODEL": "custom-qa",
        "OLLAMA_JOURNAL_MODEL": "custom-journal",
        "OLLAMA_NUM_CTX": "4096",
        "OLLAMA_NUM_PREDICT": "256",
        "OLLAMA_TIMEOUT": "60",
        "OLLAMA_KEEP_ALIVE": "5m",
    }.items():
        monkeypatch.setenv(key, value)
    provider = OllamaProvider()
    assert provider.num_ctx == 4096 and provider.timeout == 60 and provider.keep_alive == "5m"
    assert provider.num_predict == 256
    assert provider.model_for("qa") == "custom-qa"
    assert provider.model_for("journal") == "custom-journal"
    assert provider.cache_namespace != OllamaProvider(qa_model="other").cache_namespace
    assert provider.cache_namespace != OllamaProvider(journal_model="other").cache_namespace
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "512")
    assert provider.cache_namespace != OllamaProvider().cache_namespace


@pytest.mark.parametrize("value", ["0", "-1"])
def test_prediction_limit_must_be_positive(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", value)
    with pytest.raises(ValueError, match="OLLAMA_NUM_PREDICT"):
        OllamaProvider()


async def test_existing_id_and_http_errors() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {"id": "original", "function": {"name": "read", "arguments": {}}}
                        ],
                    }
                },
            )
        )
    ) as client:
        result = await OllamaProvider(client=client).complete([], [], "m")
        assert result.tool_calls[0].id == "original"
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(404, json={"error": "missing model"})
        )
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await OllamaProvider(client=client).complete([], [], "missing")
