"""Offline generated-record evaluation: python -m tsuyu_shiori.eval."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from random import Random
from typing import Any

from tsuyu_shiori.features import JST, answer_question
from tsuyu_shiori.gateway import CachedProvider, MockProvider, Provider
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
            ["バナナ", "+0.47", "コピーで20回", "接近15回"],
        ),
        ("バナナの好みは？", ["+0.47", "接近15回"]),
        ("どうしてりんご酢から離れるの？", ["コピーで20回", "回避14回"]),
        ("ごはんの大成功は？", ["大成功は1回", "#9002"]),
        ("睡眠はどうだった？", ["7.7時間", "#s-7"]),
        ("そうじの結果は？", ["スコアは80", "#9003"]),
        ("温度あわせの結果は？", ["スコアは90", "#9004"]),
        ("羽化した特性は？", ["慎重", "#9005"]),
        ("さなぎの場所えらびは？", ["該当記録がありません", "記録を残して"]),
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


async def evaluate(provider: Provider | None = None, seed: int = 37) -> dict[str, Any]:
    store, questions = synthesize(seed)
    topics = topic_questions(store)
    cases = [(q, n, "count") for q, n in questions] + [(q, parts, "topic") for q, parts in topics]
    lab = MemoryLab(store, {"eval-fly": {"banana": 0.47, "apple_vinegar": -0.4}})
    provider = provider if provider is not None else CachedProvider(MockProvider())
    results: list[dict[str, Any]] = []
    kept = dropped = 0
    for question, expected, category in cases:
        answer = await answer_question(
            question,
            store=store,
            lab=lab,
            week_id="eval-week",
            fly_id="eval-fly",
            provider=provider,
        )
        match = re.search(r"該当する記録は(\d+)回", answer.text)
        actual = (int(match[1]) if match else None) if category == "count" else answer.text
        correct = actual == expected if category == "count" else all(p in actual for p in expected)
        kept += answer.verification.kept
        dropped += answer.verification.dropped
        results.append(
            {
                "question": question,
                "category": category,
                "expected": expected,
                "actual": actual,
                "correct": correct,
                "readability": readability(answer.text, answer.verification.dropped),
                **answer.to_dict(),
            }
        )
    accuracy = sum(r["correct"] for r in results if r["category"] == "count") / len(questions)
    topic_accuracy = sum(r["correct"] for r in results if r["category"] == "topic") / len(topics)
    readability_rate = sum(r["readability"]["passed"] for r in results) / len(results)
    rate = kept / (kept + dropped) if kept + dropped else 0.0
    cost = sum(r["cost"]["usd"] for r in results) / len(results)
    return {
        "passed": accuracy >= 0.8
        and rate >= 0.95
        and topic_accuracy == 1
        and readability_rate == 1,
        "provider": provider.cache_namespace,
        "seed": seed,
        "questions": len(results),
        "accuracy": accuracy,
        "topic_accuracy": topic_accuracy,
        "readability_rate": readability_rate,
        "max_ids_per_answer": max(r["readability"]["id_count"] for r in results),
        "max_answer_length": max(r["readability"]["length"] for r in results),
        "verification_rate": rate,
        "cost_per_answer_usd": cost,
        "thresholds": {
            "accuracy": 0.8,
            "verification_rate": 0.95,
            "topic_accuracy": 1,
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
        "# Shiori offline evaluation",
        "",
        f"Passed: **{report['passed']}**",
        "",
        f"- Questions: {report['questions']}",
        f"- Accuracy: {report['accuracy']:.3f}",
        f"- Topic accuracy: {report['topic_accuracy']:.3f}",
        f"- Readability rate: {report['readability_rate']:.3f}",
        f"- Maximum IDs / characters: {report['max_ids_per_answer']} / "
        f"{report['max_answer_length']}",
        f"- Evidence verification rate: {report['verification_rate']:.3f}",
        f"- Cost per answer (USD): {report['cost_per_answer_usd']:.6f}",
        "",
        "This gate checks generated counts, expected topic observations, citation existence,",
        "and readability; it does not prove semantic entailment or live-provider quality.",
        "Mock token counts are estimates.",
        "",
    ]
    (directory / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("eval-results/shiori"))
    parser.add_argument("--seed", type=int, default=37)
    args = parser.parse_args()
    report = asyncio.run(evaluate(seed=args.seed))
    write_report(report, args.output_dir)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
