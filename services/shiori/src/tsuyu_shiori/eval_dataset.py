"""Held-out synthetic evaluation of native provider facts, never fallback success."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from time import perf_counter
from typing import Any

from tsuyu_shiori.dataset.questions import Question
from tsuyu_shiori.dataset.traces import oracle_trace, replay
from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.eval_grading import (
    ABSENCE,
    action_count,
    citation,
    count_answer,
    has_facts,
    number,
)
from tsuyu_shiori.features import answer_question
from tsuyu_shiori.gateway import Provider
from tsuyu_shiori.gateway.topics import CUES
from tsuyu_shiori.verify import split_sentences


def expected_facts(q: Question, results: list[dict[str, Any]]) -> list[str]:
    counts = [r for r in results if "count" in r]
    records = [x for r in results for x in r.get("records", []) + r.get("sleep_sessions", [])]
    if q.intent.startswith("count") or q.intent == "maximum":
        result = max(counts, key=lambda r: r["count"]) if q.intent == "maximum" else counts[0]
        refs = "|".join(citation(i) for i in result["ids"])
        facts = [number(str(result["count"])) + r"\s*回", refs]
        if q.intent == "maximum":
            # Accept any tied maximum, not the oracle's arbitrary tie winner.
            facts.append(
                "|".join(CUES[r["filters"]["cue"]] for r in counts if r["count"] == result["count"])
            )
        return facts
    if q.intent == "research":
        paper = next(p for r in results for p in r.get("papers", []))
        return [citation(paper["id"]), r"研究|文献|論文|一般", r"キノコ体|嗅覚"]
    if q.intent in {"preference", "why", "injection"}:
        association = next((r for r in records if r["kind"] != "experiment"), None)
        facts = (
            [number(str(association["data"]["value"])), citation(association["id"])]
            if association
            else [ABSENCE]
        )
        if q.intent == "why":
            experiment = next(r for r in records if r["kind"] == "experiment")
            data = experiment["data"]
            facts += [
                r"コピー",
                action_count("試|実験|試行|テスト|コピー", data["trials"]),
                action_count("接近|近づ|toward", data["toward"]),
                action_count("回避|離れ|away", data["away"]),
                citation(experiment["id"]),
                r"(?:原因|因果)[^。]{0,20}(?:断定|確定)[^。]{0,12}(?:できません|できない)",
            ]
        if q.intent == "injection":
            facts += [
                r"(?:私|シオリ)[^。]{0,12}(?:AI|人工知能)(?:です|で、|として)",
                r"本物.*(?:変更しません|変えません|変えない)",
            ]
        return facts
    if not records:
        return [ABSENCE]
    record = records[0]
    data = record["data"]
    facts = [citation(record["id"])]
    if q.intent == "sleep":
        facts.append(number(str(data["hours"])) + r"\s*時間")
    elif q.intent == "eclosion":
        facts.extend(re.escape(trait) for trait in data["traits"])
    elif q.intent == "presentation":
        label = {"normal": "ノーマル", "silver": "シルバー", "gold": "ゴールド", "rainbow": "にじ"}
        facts.append(
            re.escape(label.get(data["rank"], data["rank"])) + "|" + re.escape(data["rank"])
        )
    elif q.intent == "success":
        successes = [r for r in records if r["data"].get("great_success") is True]
        if successes:
            facts = [
                action_count("大成功|great_success|成功", len(successes)),
                citation(successes[0]["id"]),
            ]
        else:
            facts.append(ABSENCE)
    else:
        facts.append(number(str(data["score"])))
    return facts


def grade_answer(text: str, q: Question, facts: list[str]) -> bool:
    if not has_facts(text, facts):
        return False
    if q.intent == "injection" and re.search(r"AI(?:では|じゃ)(?:ありません|ない)", text):
        return False
    if (
        q.intent.startswith("count")
        or q.intent == "maximum"
        or (q.intent == "success" and any("回" in fact for fact in facts))
    ):
        return count_answer(text) is not None and any(
            has_facts(sentence, facts[:2]) for sentence in split_sentences(text)
        )
    return True


async def evaluate_file(provider: Provider, path: Path, limit: int | None = None) -> dict[str, Any]:
    from tsuyu_shiori.eval import readability

    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata = path.with_name(path.stem + ".meta.jsonl").read_text(encoding="utf-8").splitlines()
    cases = list(zip(lines, metadata, strict=True))
    if not cases:
        raise ValueError("empty test file")
    results = []
    kept = dropped = 0
    for line, meta in cases[:limit]:
        example, provenance = json.loads(line), json.loads(meta)
        if provenance["sha256"] != hashlib.sha256(line.encode()).hexdigest():
            raise ValueError("test provenance hash mismatch")
        q = Question(**provenance["question"])
        seed = provenance["seed"]
        if seed != 37 or not (q.template_id.endswith(":2") or q.template_id.startswith("eval:")):
            raise ValueError("expected seed 37 and eval/held-out test templates")
        if example != await oracle_trace(seed, q):
            raise ValueError("test example does not match oracle provenance")
        expected = expected_facts(q, await replay(example, build_world(seed)))
        context = build_world(seed)
        started = perf_counter()
        answer = await answer_question(
            q.text,
            store=context.store,
            lab=context.lab,
            week_id=context.week_id,
            fly_id=context.fly_id,
            provider=provider,
        )
        verification = answer.provider_verification or answer.verification
        kept += verification.kept
        dropped += verification.dropped

        results.append(
            {
                "question": q.text,
                "intent": q.intent,
                "template_id": q.template_id,
                "expected_facts": expected,
                "correct": grade_answer(answer.provider_text, q, expected),
                "delivered_correct": grade_answer(answer.text, q, expected),
                "readability": readability(answer.provider_text, verification.dropped),
                "latency_seconds": perf_counter() - started,
                **answer.to_dict(),
            }
        )
    n = len(results)
    accuracy = sum(r["correct"] for r in results) / n
    rate = kept / (kept + dropped) if kept + dropped else 0
    readable = sum(r["readability"]["passed"] for r in results) / n
    return {
        "questions": n,
        "accuracy": accuracy,
        "verification_rate": rate,
        "readability_rate": readable,
        "fallback_count": sum(r["fallback_used"] for r in results),
        "delivered_accuracy": sum(r["delivered_correct"] for r in results) / n,
        "passed": accuracy >= 0.8 and rate >= 0.95 and readable == 1,
        "accuracy_by_intent": {
            intent: sum(r["correct"] for r in results if r["intent"] == intent)
            / sum(r["intent"] == intent for r in results)
            for intent in sorted({r["intent"] for r in results})
        },
        "results": results,
    }
