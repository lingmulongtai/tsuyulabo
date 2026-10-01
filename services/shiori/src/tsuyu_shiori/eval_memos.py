"""Three reproducible journal-model morning memos on the synthetic week."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from tsuyu_shiori.eval import readability, synthesize
from tsuyu_shiori.features import JST, morning_memo
from tsuyu_shiori.gateway import MockProvider, OllamaProvider, Provider
from tsuyu_shiori.records import MemoryLab


async def evaluate_memos(provider: Provider | None = None) -> dict[str, Any]:
    provider = provider if provider is not None else MockProvider()
    store, _ = synthesize()
    lab = MemoryLab(store, {"eval-fly": {"banana": 0.47, "apple_vinegar": -0.4}})
    results = []
    for day in (23, 25, 28):
        now = datetime(2026, 9, day, 8, tzinfo=JST)
        started = perf_counter()
        answer = await morning_memo(
            store=store,
            lab=lab,
            week_id="eval-week",
            fly_id="eval-fly",
            now=now,
            provider=provider,
        )
        verification = answer.provider_verification or answer.verification
        results.append(
            {
                "now": now.isoformat(),
                "latency_seconds": perf_counter() - started,
                "readability": readability(answer.provider_text, verification.dropped),
                **answer.to_dict(),
            }
        )
    return {"journal_model": provider.model_for("journal"), "seed": 37, "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["mock", "ollama"], default="mock")
    parser.add_argument("--journal-model")
    parser.add_argument("--output", type=Path, default=Path("eval-results/shiori-memos.json"))
    args = parser.parse_args()
    if args.provider == "ollama" and (os.getenv("SHIORI_LIVE_EVAL") != "1" or os.getenv("CI")):
        parser.error("live evaluation requires SHIORI_LIVE_EVAL=1 and must not run in CI")
    provider = (
        OllamaProvider(journal_model=args.journal_model)
        if args.provider == "ollama"
        else MockProvider()
    )
    report = asyncio.run(evaluate_memos(provider))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
