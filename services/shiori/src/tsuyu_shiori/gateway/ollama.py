"""Stateless native Ollama chat adapter; no API keys or model-specific logic."""

from __future__ import annotations

import hashlib
import json
import os
import re
from copy import deepcopy
from typing import Any

import httpx

from .base import Cost, Response, ToolCall


class OllamaProvider:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        qa_model: str | None = None,
        journal_model: str | None = None,
    ) -> None:
        self.client = client
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip(
            "/"
        )
        self.qa_model = qa_model or os.getenv("OLLAMA_QA_MODEL", "qwen3.5:4b")
        self.journal_model = journal_model or os.getenv("OLLAMA_JOURNAL_MODEL", "qwen3.5:2b-q4_K_M")
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
        self.num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.generation_stats: list[dict[str, int]] = []
        if self.num_ctx <= 0 or self.timeout <= 0:
            raise ValueError("OLLAMA_NUM_CTX and OLLAMA_TIMEOUT must be positive")

    @property
    def cache_namespace(self) -> str:
        return f"ollama:v1:{self.base_url}:{self.qa_model}:{self.journal_model}:{self.num_ctx}"

    def model_for(self, purpose: str) -> str:
        return self.journal_model if purpose == "journal" else self.qa_model

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str
    ) -> Response:
        inputs: list[dict[str, Any]] = []
        for message in messages:
            if message["role"] == "tool":
                inputs.append(
                    {"role": "tool", "tool_name": message["name"], "content": message["content"]}
                )
            elif message.get("continuation"):
                inputs.extend(message["continuation"])
            else:
                inputs.append({"role": message["role"], "content": message["content"]})
        body = {
            "model": model,
            "messages": inputs,
            "tools": [{"type": "function", "function": tool} for tool in tools],
            "stream": False,
            "think": False,
            "keep_alive": self.keep_alive,
            "options": {"num_ctx": self.num_ctx, "temperature": 0.2},
        }
        url = f"{self.base_url}/api/chat"
        try:
            if self.client is not None:
                result = await self.client.post(url, json=body, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    result = await client.post(url, json=body)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Cannot connect to Ollama at {url}; start Ollama on the host"
            ) from exc
        result.raise_for_status()
        data = result.json()
        self.generation_stats.append(
            {key: data.get(key, 0) for key in ("eval_count", "eval_duration", "load_duration")}
        )
        native = deepcopy(data["message"])
        text = re.sub(r"<think>.*?</think>", "", native.get("content", ""), flags=re.S).strip()
        native["content"] = text
        calls: list[ToolCall] = []
        for index, call in enumerate(native.get("tool_calls", [])):
            function = call["function"]
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if not isinstance(arguments, dict):
                raise ValueError("Ollama tool arguments must be a JSON object")
            function["arguments"] = arguments
            fingerprint = json.dumps([len(messages), index, function], sort_keys=True)
            call_id = (
                call.get("id") or "call_" + hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
            )
            call["id"] = call_id
            calls.append(ToolCall(call_id, function["name"], arguments))
        return Response(
            text,
            calls,
            Cost(data.get("prompt_eval_count", 0), data.get("eval_count", 0)),
            [native],
        )
