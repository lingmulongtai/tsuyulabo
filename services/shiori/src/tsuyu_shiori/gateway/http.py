"""Raw HTTP adapters; injected clients make wire contracts testable without API keys."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from .base import Cost, Response, ToolCall


class HTTPProvider:
    vendor: str
    default_journal: str
    default_qa: str
    default_rates: tuple[float, float]

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
        journal_model: str | None = None,
        qa_model: str | None = None,
        rates: tuple[float, float] | None = None,
    ) -> None:
        prefix = self.vendor.upper()
        self.api_key = api_key or os.environ.get(f"{prefix}_API_KEY", "")
        self.client = client
        self.journal_model = (
            journal_model or os.getenv(f"{prefix}_JOURNAL_MODEL") or self.default_journal
        )
        self.qa_model = qa_model or os.getenv(f"{prefix}_QA_MODEL") or self.default_qa
        # Deliberately conservative estimates, configurable for the selected models.
        self.rates = rates or (
            float(os.getenv(f"{prefix}_INPUT_USD_PER_MILLION", str(self.default_rates[0]))),
            float(os.getenv(f"{prefix}_OUTPUT_USD_PER_MILLION", str(self.default_rates[1]))),
        )

    @property
    def cache_namespace(self) -> str:
        return f"{self.vendor}:v1:{self.rates}"

    def model_for(self, purpose: str) -> str:
        return self.journal_model if purpose == "journal" else self.qa_model

    def cost(self, input_tokens: int, output_tokens: int) -> Cost:
        return Cost(
            input_tokens,
            output_tokens,
            (input_tokens * self.rates[0] + output_tokens * self.rates[1]) / 1_000_000,
        )

    async def post(self, url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError(f"{self.vendor.upper()}_API_KEY is required")
        if self.client is not None:
            result = await self.client.post(url, headers=headers, json=body, timeout=30)
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                result = await client.post(url, headers=headers, json=body)
        result.raise_for_status()
        return result.json()


class OpenAIProvider(HTTPProvider):
    vendor = "openai"
    default_journal = "gpt-4.1-nano"
    default_qa = "gpt-4.1-mini"
    default_rates = (0.4, 1.6)

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str
    ) -> Response:
        inputs: list[dict[str, Any]] = []
        for message in messages:
            if message["role"] == "tool":
                inputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": message["call_id"],
                        "output": message["content"],
                    }
                )
            elif message.get("continuation"):
                inputs.extend(message["continuation"])
            else:
                inputs.append({"role": message["role"], "content": message["content"]})
        body = {
            "model": model,
            "input": inputs,
            "store": False,
            "max_output_tokens": 1200,
            "tools": [{"type": "function", **tool, "strict": False} for tool in tools],
        }
        data = await self.post(
            "https://api.openai.com/v1/responses", {"Authorization": f"Bearer {self.api_key}"}, body
        )
        calls: list[ToolCall] = []
        texts: list[str] = []
        for item in data.get("output", []):
            if item["type"] == "function_call":
                calls.append(ToolCall(item["call_id"], item["name"], json.loads(item["arguments"])))
            elif item["type"] == "message":
                texts.extend(
                    block["text"] for block in item["content"] if block["type"] == "output_text"
                )
        usage = data.get("usage", {})
        return Response(
            "".join(texts),
            calls,
            self.cost(usage.get("input_tokens", 0), usage.get("output_tokens", 0)),
            data.get("output", []),
        )


class AnthropicProvider(HTTPProvider):
    vendor = "anthropic"
    default_journal = "claude-haiku-4-5"
    default_qa = "claude-sonnet-4-6"
    default_rates = (3.0, 15.0)

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str
    ) -> Response:
        inputs: list[dict[str, Any]] = []
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        for message in messages:
            if message["role"] == "system":
                continue
            if message["role"] == "tool":
                block = {
                    "type": "tool_result",
                    "tool_use_id": message["call_id"],
                    "content": message["content"],
                }
                if (
                    inputs
                    and inputs[-1]["role"] == "user"
                    and isinstance(inputs[-1]["content"], list)
                ):
                    inputs[-1]["content"].append(block)
                else:
                    inputs.append({"role": "user", "content": [block]})
            else:
                inputs.append(
                    {
                        "role": message["role"],
                        "content": message.get("continuation") or message["content"],
                    }
                )
        body = {
            "model": model,
            "system": system,
            "messages": inputs,
            "max_tokens": 1200,
            "tools": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "input_schema": t["parameters"],
                }
                for t in tools
            ],
        }
        data = await self.post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            body,
        )
        calls: list[ToolCall] = []
        texts: list[str] = []
        for item in data.get("content", []):
            if item["type"] == "tool_use":
                calls.append(ToolCall(item["id"], item["name"], item["input"]))
            elif item["type"] == "text":
                texts.append(item["text"])
        usage = data.get("usage", {})
        return Response(
            "".join(texts),
            calls,
            self.cost(usage.get("input_tokens", 0), usage.get("output_tokens", 0)),
            data.get("content", []),
        )
