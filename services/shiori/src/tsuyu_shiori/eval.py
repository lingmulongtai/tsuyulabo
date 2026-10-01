"""Generated-record evaluation (offline by default): python -m tsuyu_shiori.eval."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from random import Random
from time import perf_counter
from typing import Any

from tsuyu_shiori.eval_grading import (
    ABSENCE,
    APPROACH,
    AVOID,
    COLLECT,
    SUCCESS,
    TRIALS,
    citation,
    count_answer,
    has_facts,
    number,
)
from tsuyu_shiori.eval_metrics import token_metrics
from tsuyu_shiori.eval_open import open_questions
from tsuyu_shiori.features import JST, answer_question
from tsuyu_shiori.gateway import CachedProvider, MockProvider, OllamaProvider, Provider
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.verify import ID_PATTERN, split_sentences


def synthesize(seed: int = 37) -> tuple[MemoryRecordStore, list[tuple[str, int]]]:
    rng = Random(seed)
    records: list[Record] = []
    questions: list[tuple[str, int]] = []
    start = datetime(2026, 9, 21, 9, tzinfo=JST)
    for day in range(1, 8):
        at = start + timedelta(days=day - 1)
        for cue, label in (
            ("banana", "バナナ"),
            ("apple_vinegar", "りんご酢"),
            ("grape", "ぶどう"),
        ):
            for valence, name in (("reward", "報酬"), ("punish", "罰")):
                count = rng.randrange(4)
                for _ in range(count):
                    records.append(
                        Record(
                            f"#{len(records) + 1:04}",
                            "training",
                            {
                                "research_day": day,
                                "cue": cue,
                                "valence": valence,
                                "value": 0.4 if valence == "reward" else -0.4,
                            },
                            "eval-week",
                            "eval-fly",
                            at,
                        )
                    )
                questions.append((f"{day}日目に{label}で{name}を覚えた回数は何回？", count))
        records.append(
            Record(
                f"#{len(records) + 1:04}",
                "meal",
                {"research_day": day},
                "eval-week",
                "eval-fly",
                at,
            )
        )
        records.append(
            Record(
                f"#s-{day}",
                "sleep",
                {"hours": 7 + day / 10},
                "eval-week",
                occurred_at=at + timedelta(hours=13),
            )
        )
    return MemoryRecordStore(records), questions


def topic_questions(store: MemoryRecordStore) -> list[tuple[str, list[str]]]:
    """Fixed observations complement randomized count questions with topic coverage."""
    for record in [
        Record(
            "#9001",
            "training",
            {"cue": "banana", "valence": "reward", "value": 0.47},
            "eval-week",
            "eval-fly",
            datetime(2026, 9, 29, tzinfo=JST),
        ),
        Record("#9002", "meal", {"great_success": True}, "eval-week"),
        Record("#9003", "cleaning", {"score": 80}, "eval-week"),
        Record("#9004", "temperature", {"score": 90}, "eval-week"),
        Record("#9005", "eclosion", {"traits": ["慎重"]}, "eval-week"),
    ]:
        store.add(record)
    return [
        (
            "しつけをすると、ツユの脳はどう変わるの？",
            ["バナナ", number("0.47"), TRIALS, APPROACH],
        ),
        ("バナナの好みは？", [number("0.47"), APPROACH]),
        ("どうしてりんご酢から離れるの？", [TRIALS, AVOID]),
        ("ごはんの大成功は？", [SUCCESS, citation("#9002")]),
        ("睡眠はどうだった？", [number("7.7") + r"\s*時間", citation("#s-7")]),
        ("そうじの結果は？", [number("80"), citation("#9003")]),
        ("温度あわせの結果は？", [number("90"), citation("#9004")]),
        ("羽化した特性は？", ["慎重", citation("#9005")]),
        ("さなぎの場所えらびは？", [ABSENCE, COLLECT]),
    ]


def readability(text: str, dropped: int = 0) -> dict[str, Any]:
    sentences = split_sentences(text)
    counts = [len(ID_PATTERN.findall(sentence)) for sentence in sentences]
    return {
        "passed": bool(sentences)
        and dropped == 0
        and len(text) <= 160
        and sum(counts) <= 6
        and all(1 <= count <= 4 for count in counts),
        "id_count": sum(counts),
        "length": len(text),
        "each_sentence_cited": bool(counts) and all(counts) and dropped == 0,
    }


async def evaluate(
    provider: Provider | None = None,
    seed: int = 37,
    *,
    limit: int | None = None,
    progress: bool = False,
) -> dict[str, Any]:
    store, questions = synthesize(seed)
    topics = topic_questions(store)
    cases = [(q, n, "count") for q, n in questions] + [(q, parts, "topic") for q, parts in topics]
    cases += [(q, facts, "open") for q, facts in open_questions(store)]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        cases = cases[:limit]
    lab = MemoryLab(store, {"eval-fly": {"banana": 0.47, "apple_vinegar": -0.4}})
    provider = provider if provider is not None else CachedProvider(MockProvider())
    stats_start = len(getattr(provider, "generation_stats", []))
    results: list[dict[str, Any]] = []
    kept = dropped = 0
    for index, (question, expected, category) in enumerate(cases, 1):
        started = perf_counter()
        answer = await answer_question(
            question,
            store=store,
            lab=lab,
            week_id="eval-week",
            fly_id="eval-fly",
            provider=provider,
        )
        latency = perf_counter() - started
        native = answer.provider_text
        actual = count_answer(native) if category == "count" else native
        delivered = count_answer(answer.text) if category == "count" else answer.text
        correct = actual == expected if category == "count" else has_facts(actual, expected)
        delivered_correct = (
            delivered == expected if category == "count" else has_facts(delivered, expected)
        )
        verification = answer.provider_verification or answer.verification
        kept += verification.kept
        dropped += verification.dropped
        if progress:
            print(
                f"[{index}/{len(cases)}] {latency:.2f}s correct={correct} "
                f"fallback={answer.fallback_used} {question}",
                file=sys.stderr,
                flush=True,
            )
        results.append(
            {
                "question": question,
                "category": category,
                "expected": expected,
                "actual": actual,
                "correct": correct,
                "delivered_correct": delivered_correct,
                "latency_seconds": latency,
                "readability": readability(native, verification.dropped),
                **answer.to_dict(),
            }
        )

    def accuracy_for(category: str, key: str = "correct") -> float:
        selected = [r for r in results if r["category"] == category]
        return sum(r[key] for r in selected) / len(selected) if selected else 0.0

    accuracy = accuracy_for("count")
    topic_accuracy = accuracy_for("topic")
    latencies = sorted(r["latency_seconds"] for r in results)
    fallback_count = sum(r["fallback_used"] for r in results)
    readability_rate = sum(r["readability"]["passed"] for r in results) / len(results)
    rate = kept / (kept + dropped) if kept + dropped else 0.0
    cost = sum(r["cost"]["usd"] for r in results) / len(results)
    generation = getattr(provider, "generation_stats", [])[stats_start:]
    duration = sum(item["eval_duration"] for item in generation) / 1_000_000_000
    return {
        "passed": accuracy >= 0.8
        and rate >= 0.95
        and topic_accuracy == 1
        and accuracy_for("open") >= 0.7
        and readability_rate == 1,
        "provider": provider.cache_namespace,
        "seed": seed,
        "qa_model": provider.model_for("qa"),
        "journal_model": provider.model_for("journal"),
        "limit": limit,
        "fallback_count": fallback_count,
        "fallback_rate": fallback_count / len(results),
        "delivered_accuracy": accuracy_for("count", "delivered_correct"),
        "delivered_topic_accuracy": accuracy_for("topic", "delivered_correct"),
        "delivered_open_accuracy": accuracy_for("open", "delivered_correct"),
        "latency_mean_seconds": sum(latencies) / len(latencies),
        "latency_p95_seconds": latencies[math.ceil(len(latencies) * 0.95) - 1],
        "input_tokens": sum(r["cost"]["input_tokens"] for r in results),
        "output_tokens": sum(r["cost"]["output_tokens"] for r in results),
        "generation_tokens_per_second": (
            sum(item["eval_count"] for item in generation) / duration if duration else None
        ),
        "load_seconds": sum(item["load_duration"] for item in generation) / 1_000_000_000,
        "generation_limit_count": sum(item.get("generation_limited", 0) for item in generation),
        "questions": len(results),
        "accuracy": accuracy,
        "topic_accuracy": topic_accuracy,
        "open_accuracy": accuracy_for("open"),
        **token_metrics(results),
        "readability_rate": readability_rate,
        "max_ids_per_answer": max(r["readability"]["id_count"] for r in results),
        "max_answer_length": max(r["readability"]["length"] for r in results),
        "verification_rate": rate,
        "cost_per_answer_usd": cost,
        "thresholds": {
            "accuracy": 0.8,
            "verification_rate": 0.95,
            "topic_accuracy": 1,
            "open_accuracy": 0.7,
            "readability_rate": 1,
            "max_ids_per_answer": 6,
            "max_answer_length": 160,
        },
        "results": results,
    }


def write_report(report: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Shiori evaluation",
        "",
        f"Passed: **{report['passed']}**",
        "",
        f"- Questions: {report['questions']}",
        f"- Accuracy: {report['accuracy']:.3f}",
        f"- Topic accuracy: {report['topic_accuracy']:.3f}",
        f"- Open accuracy: {report['open_accuracy']:.3f}",
        f"- Readability rate: {report['readability_rate']:.3f}",
        f"- Maximum IDs / characters: {report['max_ids_per_answer']} / "
        f"{report['max_answer_length']}",
        f"- Evidence verification rate: {report['verification_rate']:.3f}",
        f"- Cost per answer (USD): {report['cost_per_answer_usd']:.6f}",
        "",
        f"- Fallbacks: {report['fallback_count']} ({report['fallback_rate']:.1%})",
        f"- Latency mean / p95 (seconds): {report['latency_mean_seconds']:.2f} / "
        f"{report['latency_p95_seconds']:.2f}",
        f"- Input / output tokens: {report['input_tokens']} / {report['output_tokens']}",
        "",
        f"- Input tokens per question mean / max: "
        f"{report['input_tokens_mean_per_question']:.1f} / "
        f"{report['input_tokens_max_per_question']}",
        f"- Maximum input tokens per model call: {report['input_tokens_max_per_call']}",
        "",
        "Question input sums every model call; context occupancy is per call.",
        "Accuracy, verification and readability grade original provider output before fallback.",
        "This gate checks generated counts, expected topic observations, citation existence,",
        "and readability; it does not prove semantic entailment or live-provider quality.",
        "Mock token counts are estimates.",
        "",
    ]
    (directory / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--provider", choices=["mock", "ollama"], default="mock")
    parser.add_argument("--qa-model")
    parser.add_argument("--journal-model")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--test-file", type=Path, help="also score oracle JSONL and its .meta.jsonl"
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.provider == "ollama" and (os.getenv("SHIORI_LIVE_EVAL") != "1" or os.getenv("CI")):
        parser.error("live evaluation requires SHIORI_LIVE_EVAL=1 and must not run in CI")
    provider = (
        OllamaProvider(qa_model=args.qa_model, journal_model=args.journal_model)
        if args.provider == "ollama"
        else CachedProvider(MockProvider())
    )
    model = provider.model_for("qa")
    safe_model = "".join(c if c.isalnum() or c in "-_." else "-" for c in model)
    directory = args.output_dir or Path(f"eval-results/shiori-{args.provider}-{safe_model}")
    report = asyncio.run(evaluate(provider, seed=args.seed, limit=args.limit, progress=True))
    if args.test_file is not None:
        from tsuyu_shiori.eval_dataset import evaluate_file

        report["heldout"] = asyncio.run(evaluate_file(provider, args.test_file, limit=args.limit))
        # Keep the existing 61-question gate unchanged; the extra score is diagnostic.
        summary = {k: v for k, v in report["heldout"].items() if k != "results"}
        print(json.dumps({"heldout": summary}, ensure_ascii=False, indent=2))
    write_report(report, directory)
    print(
        json.dumps({k: v for k, v in report.items() if k not in {"results", "heldout"}}, indent=2)
    )
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
