"""Ideal native tool-use conversations, checked before they leave the generator."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from tsuyu_shiori.agent.prompt import SYSTEM_PROMPT
from tsuyu_shiori.dataset.counts import count_answer, count_calls
from tsuyu_shiori.dataset.observations import observation_answer, observation_calls
from tsuyu_shiori.dataset.questions import Question
from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.eval import readability
from tsuyu_shiori.tools import SCHEMAS, ToolContext, execute
from tsuyu_shiori.verify import verify


def evidence(results: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    papers = {p["id"] for r in results for p in r.get("papers", [])}
    ids = papers | {i for r in results for i in r.get("ids", [])}
    ids |= {x["id"] for r in results for x in r.get("records", []) + r.get("sleep_sessions", [])}
    return ids, papers


async def oracle_trace(seed: int, q: Question) -> dict[str, Any]:
    context = build_world(seed)
    counting = q.intent.startswith("count") or q.intent == "maximum"
    calls = (
        count_calls(q, context.week_id)
        if counting
        else observation_calls(q, context.week_id, context.fly_id)
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "question": q.text,
                    "feature": "answer",
                    "week_id": context.week_id,
                    "fly_id": context.fly_id,
                },
                ensure_ascii=False,
            ),
        },
    ]
    results = []
    for start in range(0, len(calls), 4):
        batch = calls[start : start + 4]
        tool_calls = [
            {
                "id": f"call_{start + i}",
                "type": "function",
                "function": {"name": name, "arguments": deepcopy(args)},
            }
            for i, (name, args) in enumerate(batch)
        ]
        messages.append({"role": "assistant", "content": "", "tool_calls": tool_calls})
        for call, (name, args) in zip(tool_calls, batch, strict=True):
            result = await execute(context, name, args)
            results.append(result)
            messages.append(
                {
                    "role": "tool",
                    "name": name,
                    "tool_call_id": call["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
    pattern = (seed + sum(map(ord, q.text))) % 3
    final = (
        count_answer(q, results, pattern) if counting else observation_answer(q, results, pattern)
    )
    allowed, papers = evidence(results)
    checked = await verify(final, context.store, allowed_ids=allowed, paper_ids=papers)
    if checked.text != final or not readability(final, checked.report.dropped)["passed"]:
        raise ValueError(f"invalid oracle answer: {seed} {q.intent} {final}")
    messages.append({"role": "assistant", "content": final})
    return {
        "messages": messages,
        "tools": [{"type": "function", "function": deepcopy(s)} for s in SCHEMAS],
    }


async def replay(example: dict[str, Any], context: ToolContext) -> list[dict[str, Any]]:
    """Reject altered tool results; execute each call on a fresh synthetic world."""
    pending: dict[str, dict[str, Any]] = {}
    results = []
    for message in example["messages"]:
        for call in message.get("tool_calls", []):
            if call["id"] in pending:
                raise ValueError("duplicate pending call")
            f = call["function"]
            pending[call["id"]] = await execute(context, f["name"], f["arguments"])
        if message["role"] == "tool":
            result = pending.pop(message["tool_call_id"])
            if result != json.loads(message["content"]):
                raise ValueError("tool replay differs from exported result")
            results.append(result)
    if pending:
        raise ValueError("unanswered tool calls")
    allowed, papers = evidence(results)
    final = example["messages"][-1]["content"]
    checked = await verify(final, context.store, allowed_ids=allowed, paper_ids=papers)
    if checked.text != final or checked.report.dropped or not readability(final)["passed"]:
        raise ValueError("invalid final answer")
    return results
