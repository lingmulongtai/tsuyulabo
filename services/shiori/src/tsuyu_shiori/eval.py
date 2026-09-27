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


async def evaluate(provider: Provider | None = None, seed: int = 37) -> dict[str, Any]:
    store, questions = synthesize(seed)
    lab = MemoryLab(store, {"eval-fly": {"banana": 0.4, "apple_vinegar": -0.4}})
    provider = provider if provider is not None else CachedProvider(MockProvider())
    results: list[dict[str, Any]] = []
    kept = dropped = 0
    for question, expected in questions:
        answer = await answer_question(
            question,
            store=store,
            lab=lab,
            week_id="eval-week",
            fly_id="eval-fly",
            provider=provider,
        )
        match = re.search(r"該当する記録は(\d+)回", answer.text)
        actual = int(match[1]) if match else None
        kept += answer.verification.kept
        dropped += answer.verification.dropped
        results.append(
            {
                "question": question,
                "expected": expected,
                "actual": actual,
                "correct": actual == expected,
                **answer.to_dict(),
            }
        )
    accuracy = sum(r["correct"] for r in results) / len(results)
    rate = kept / (kept + dropped) if kept + dropped else 0.0
    cost = sum(r["cost"]["usd"] for r in results) / len(results)
    return {
        "passed": accuracy >= 0.8 and rate >= 0.95,
        "provider": provider.cache_namespace,
        "seed": seed,
        "questions": len(results),
        "accuracy": accuracy,
        "verification_rate": rate,
        "cost_per_answer_usd": cost,
        "thresholds": {"accuracy": 0.8, "verification_rate": 0.95},
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
        f"- Evidence verification rate: {report['verification_rate']:.3f}",
        f"- Cost per answer (USD): {report['cost_per_answer_usd']:.6f}",
        "",
        "This gate checks generated count questions and citation existence, not semantic",
        "entailment or live-provider quality. Mock token counts are estimates.",
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
