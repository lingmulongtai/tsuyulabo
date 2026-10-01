"""Dependency-free chat validation and assistant token masking for the GPU scripts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def validate_example(row: dict[str, Any]) -> None:
    if set(row) != {"messages", "tools"}:
        raise ValueError("expected exactly messages and tools")
    names = set()
    for tool in row["tools"]:
        if tool.get("type") != "function" or not isinstance(tool.get("function"), dict):
            raise ValueError("invalid function schema")
        f = tool["function"]
        if not isinstance(f.get("parameters"), dict) or not isinstance(f.get("name"), str):
            raise ValueError("function schema needs name and parameters")
        names.add(f["name"])
    messages = row["messages"]
    if len(messages) < 5 or [m["role"] for m in messages[:2]] != ["system", "user"]:
        raise ValueError("expected system, user, calls, results, final")
    if messages[-1]["role"] != "assistant" or not messages[-1].get("content"):
        raise ValueError("missing assistant final")
    payload = json.loads(messages[1]["content"])
    if set(payload) != {"question", "feature", "week_id", "fly_id"}:
        raise ValueError("invalid agent user payload")
    pending: dict[str, str] = {}
    seen = set()
    for m in messages[2:]:
        if not isinstance(m.get("content"), str):
            raise ValueError("content must be a string")
        if m["role"] == "assistant":
            if pending:
                raise ValueError("assistant before outstanding tool results")
            calls = m.get("tool_calls", [])
            if len(calls) > 4:
                raise ValueError("agent allows at most four tools per turn")
            for call in calls:
                f = call["function"]
                if call.get("type") != "function" or f["name"] not in names:
                    raise ValueError("invalid tool call")
                if not isinstance(f["arguments"], dict) or call["id"] in seen:
                    raise ValueError("arguments must be an object; IDs must be unique")
                seen.add(call["id"])
                pending[call["id"]] = f["name"]
        elif m["role"] == "tool":
            if pending.pop(m.get("tool_call_id"), None) != m.get("name"):
                raise ValueError("tool result does not match a pending call")
            if not isinstance(json.loads(m["content"]), dict):
                raise ValueError("tool result must be a JSON object")
        else:
            raise ValueError("unexpected role after user")
    if pending or not seen or messages[-1].get("tool_calls"):
        raise ValueError("incomplete conversation")


def load_data(directory: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    stats = json.loads((directory / "stats.json").read_text(encoding="utf-8"))
    rows = {}
    seeds: dict[str, set[int]] = {}
    templates: dict[str, set[str]] = {}
    for split in ("train", "valid", "test"):
        lines = (directory / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        provenance = [
            json.loads(line)
            for line in (directory / f"{split}.meta.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        if not lines or len(lines) != stats["splits"][split]["examples"]:
            raise ValueError(f"{split}: empty or stats count mismatch")
        hashes = []
        rows[split] = []
        for line, meta in zip(lines, provenance, strict=True):
            digest = hashlib.sha256(line.encode()).hexdigest()
            if digest != meta["sha256"]:
                raise ValueError(f"{split}: provenance hash mismatch")
            row = json.loads(line)
            validate_example(row)
            rows[split].append(row)
            hashes.append(digest)
        if hashlib.sha256("".join(hashes).encode()).hexdigest() != stats["splits"][split]["sha256"]:
            raise ValueError(f"{split}: split hash mismatch")
        seeds[split] = {p["seed"] for p in provenance}
        templates[split] = {p["question"]["template_id"] for p in provenance}
        if seeds[split] != set(stats["splits"][split]["seeds"]):
            raise ValueError("seed manifest mismatch")
        if templates[split] != set(stats["splits"][split]["templates"]):
            raise ValueError("template manifest mismatch")
    for a, b in (("train", "valid"), ("train", "test"), ("valid", "test")):
        if seeds[a] & seeds[b]:
            raise ValueError("overlapping seed splits")
    if any(
        t.endswith(":2") or t.startswith("eval:") for t in templates["train"] | templates["valid"]
    ):
        raise ValueError("held-out template leaked into training/validation")
    if not isinstance(stats.get("max_length"), int) or not 1 <= stats["max_length"] <= 3072:
        raise ValueError("stats max_length must be 1..3072")
    return rows, stats


def encode_assistant(row: dict[str, Any], tokenizer: Any, max_length: int) -> dict[str, Any]:
    """Use Qwen's native tool template; mask system/user/tool tokens, including their IDs."""
    rendered = tokenizer.apply_chat_template(
        row["messages"],
        tools=row["tools"],
        tokenize=False,
        add_generation_prompt=False,
        enable_thinking=False,
    )
    # Qwen3.5's template lacks generation tags on some releases. Offsets keep the
    # exact original inference template and avoid brittle prefix-token subtraction.
    spans = [
        (m.start(1), m.end())
        for m in re.finditer(
            r"<\|im_start\|>assistant[^\n]*\n(.*?)<\|im_end\|>", rendered, re.DOTALL
        )
    ]
    expected = sum(m["role"] == "assistant" for m in row["messages"])
    if len(spans) != expected:
        raise ValueError("unexpected Qwen assistant delimiters; inspect the model chat template")
    encoded = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    if len(encoded["input_ids"]) > max_length:
        raise ValueError(
            f"actual tokens {len(encoded['input_ids'])} exceed max_length {max_length}; "
            "regenerate shorter traces or raise stats max_length; never truncate labels"
        )
    labels = [
        token if any(start <= a < end and b <= end for start, end in spans) else -100
        for token, (a, b) in zip(encoded["input_ids"], encoded["offset_mapping"], strict=True)
    ]
    if not any(label != -100 for label in labels):
        raise ValueError("no assistant supervision")
    return {
        "input_ids": encoded["input_ids"],
        "attention_mask": encoded["attention_mask"],
        "labels": labels,
    }
