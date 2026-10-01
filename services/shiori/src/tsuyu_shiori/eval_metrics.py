"""Token accounting distinguishes cumulative question input from a single context."""

from __future__ import annotations

from typing import Any


def token_metrics(results: list[dict[str, Any]]) -> dict[str, float | int]:
    inputs = [r["cost"]["input_tokens"] for r in results]
    calls = [call["input_tokens"] for r in results for call in r["cost"]["calls"]]
    return {
        "input_tokens_mean_per_question": sum(inputs) / len(inputs) if inputs else 0.0,
        "input_tokens_max_per_question": max(inputs, default=0),
        "input_tokens_max_per_call": max(calls, default=0),
    }
