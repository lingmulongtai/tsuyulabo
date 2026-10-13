"""Fact-graded companion evaluation, including raw candidate output before fallback."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any

from tsuyu_shiori.companion import phrase
from tsuyu_shiori.dataset.companion import companion_questions, companion_trace, observation
from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.diary_events import notable_events
from tsuyu_shiori.features import JST
from tsuyu_shiori.gateway import MockProvider, Provider
from tsuyu_shiori.hint_rules import detect_trouble
from tsuyu_shiori.records import MemoryRecordStore, Record
from tsuyu_shiori.verify import extract_ids, split_sentences, verify


def facts_for_payload(payload: dict[str, Any]) -> list[str]:
    feature = payload["feature"]
    if feature == "diary":
        text = " ".join(m["description"] for m in payload["moments"])
        facts = []
        for word, pattern in (
            ("ごはん", "ごはん|餌"),
            ("飛", "飛|飛行"),
            ("バナナ", "バナナ"),
            ("羽化", "羽化"),
        ):
            if word in text:
                facts.append(pattern)
        return facts
    if feature == "hint":
        text = payload["observation"] + payload["help"]
        for word, patterns in (
            ("暑", ["暑|高温", "下げ|涼"]),
            ("冷", ["冷|低温", "上げ|暖"]),
            ("カビ", ["カビ", "そうじ|除|掃除"]),
            ("乾", ["乾", "しっとり|ごはん"]),
            ("時間", ["ごはん|食事", "用意|食"]),
            ("逃", ["逃", "確かめ|確認"]),
        ):
            if word in text:
                return patterns
    if feature == "behaviour-why":
        facts = [re.escape(payload["observation"]["label"]), "脳|出力"]
        if "まだ" in payload["context_text"] or "未記録" in payload["context_text"]:
            facts.append("まだ|未記録|記録がありません")
        return facts
    return []


def grade(text: str, payload: dict[str, Any], evidence: list[str]) -> bool:
    if not all(re.search(fact, text) for fact in facts_for_payload(payload)):
        return False
    if not extract_ids(text) or not set(extract_ids(text)) <= set(evidence):
        return False
    limits = {"diary": (2, 3), "hint": (1, 1), "behaviour-why": (1, 2), "morning": (2, 3)}
    low, high = limits[payload["feature"]]
    if not low <= len(split_sentences(text)) <= high:
        return False
    # An existing ID cannot justify an invented association value.
    return not (
        payload["feature"] == "behaviour-why"
        and ("未記録" in payload["context_text"] or "まだ" in payload["context_text"])
        and re.search(r"(?:好み|連合)[^。#]{0,16}[+-]?\d+(?:\.\d+)?", text)
    )


async def evaluate_trace(provider: Provider, seed: int, q: Any) -> dict[str, Any]:
    example = await companion_trace(seed, q)
    context = build_world(seed)
    context.store.add(observation(seed))
    payload = json.loads(example["messages"][1]["content"])
    evidence = extract_ids(example["messages"][-1]["content"])
    response = await provider.complete(example["messages"][:-1], [], provider.model_for("journal"))
    checked = await verify(response.text, context.store, allowed_ids=set(evidence))
    correct = grade(response.text, payload, evidence) and not checked.report.dropped
    if q.intent == "morning":
        # Morning traces must preserve the actual sleep length as well as its ID.
        tool = json.loads(next(m["content"] for m in example["messages"] if m["role"] == "tool"))
        hours = tool["sleep_sessions"][0]["data"]["hours"]
        correct = correct and f"{hours:.1f}" in response.text
    return {
        "intent": q.intent,
        "correct": correct,
        "text": response.text,
        "verification": checked.report.to_dict(),
    }


async def evaluate_companion(provider: Provider | None = None) -> dict[str, Any]:
    provider = provider or MockProvider()
    results = [await evaluate_trace(provider, 37, q) for q in companion_questions(2)]
    now = datetime(2026, 10, 13, 12, tzinfo=JST)
    store = MemoryRecordStore([Record("#0001", "habitat_observation", {}, "w", "f", now)])
    states = [
        {"temperature": 32},
        {"temperature": 16},
        {"mould": 0.4},
        {"food": {"moisture": 0.1}},
        {"fed_at": (now - timedelta(hours=13)).isoformat()},
        {"behaviour": "escape"},
    ]
    for state in states:
        trouble = detect_trouble(state, now)
        payload = {
            "feature": "hint",
            "observation": trouble.observation,
            "help": trouble.help,
            "evidence": ["#0001"],
        }
        answer = await phrase(
            "hint", payload, store, ["#0001"], provider=provider, evaluate_candidate=True
        )
        results.append(
            {
                "intent": "hint",
                "correct": grade(answer.provider_text, payload, ["#0001"]),
                "text": answer.provider_text,
                "verification": answer.provider_verification.to_dict(),
            }
        )
    for cue in ("酵母", "青い光"):
        payload = {
            "feature": "behaviour-why",
            "observation": {"id": "#0001", "behaviour": "walk", "label": "歩く"},
            "context_text": f"{cue}の好みはまだ未記録です #0001。",
            "context_evidence": ["#0001"],
        }
        answer = await phrase(
            "behaviour-why", payload, store, ["#0001"], provider=provider, evaluate_candidate=True
        )
        results.append(
            {
                "intent": "behaviour-why",
                "correct": grade(answer.provider_text, payload, ["#0001"]),
                "text": answer.provider_text,
                "verification": answer.provider_verification.to_dict(),
            }
        )
    records = [
        Record("#0001", "training", {"cue": "banana", "valence": "reward"}, "w", "f", now),
        Record(
            "#0002",
            "behaviour",
            {"behaviour": "approach", "cue": "banana", "stage": "adult"},
            "w",
            "f",
            now + timedelta(minutes=1),
        ),
    ]
    store = MemoryRecordStore(records)
    moments = notable_events(records, now.replace(hour=0), now + timedelta(days=1))
    payload = {
        "feature": "diary",
        "moments": [{"description": m.description, "evidence": m.evidence} for m in moments],
    }
    ids = [i for m in moments for i in m.evidence]
    answer = await phrase("diary", payload, store, ids, provider=provider, evaluate_candidate=True)
    results.append(
        {
            "intent": "diary",
            "correct": grade(answer.provider_text, payload, ids)
            and bool(re.search("寄|接近", answer.provider_text)),
            "text": answer.provider_text,
            "verification": answer.provider_verification.to_dict(),
        }
    )
    return {
        "passed": all(r["correct"] and r["verification"]["rate"] == 1 for r in results),
        "accuracy": sum(r["correct"] for r in results) / len(results),
        "questions": len(results),
        "results": results,
    }
