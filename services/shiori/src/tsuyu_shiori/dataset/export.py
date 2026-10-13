"""Disjoint seeded splits with replay provenance kept outside training messages."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from tsuyu_shiori.dataset.companion import INTENTS, companion_questions, companion_trace
from tsuyu_shiori.dataset.questions import Question, balanced_questions, questions
from tsuyu_shiori.dataset.traces import oracle_trace
from tsuyu_shiori.eval import open_questions, synthesize, topic_questions


def token_estimate(example: dict[str, Any]) -> int:
    # Includes complete tool schemas. An estimate, not Qwen tokenizer output.
    text = json.dumps(example, ensure_ascii=False)
    non_ascii = sum(ord(c) > 127 for c in text)
    return math.ceil((len(text) - non_ascii) / 4 + non_ascii * 1.5)


def eval_questions() -> list[Question]:
    """All 61 existing eval questions, retaining their exact original wording."""
    store, counts = synthesize(37)
    result = []
    for i, (text, _) in enumerate(counts):
        day = i // 6 + 1
        cue = ("banana", "apple_vinegar", "grape")[(i % 6) // 2]
        valence = ("reward", "punish")[i % 2]
        result.append(
            Question("count_day", text, "eval:count", {"day": day, "cue": cue, "valence": valence})
        )
    topics = topic_questions(store)
    opens = open_questions(store)
    intents = [
        "why",
        "preference",
        "why",
        "success",
        "sleep",
        "cleaning",
        "temperature",
        "eclosion",
        "pupation_site",
        "why",
        "why",
        "preference",
        "sleep",
        "presentation",
        "maximum",
        "success",
        "cleaning",
        "temperature",
        "eclosion",
    ]
    for i, ((text, _), intent) in enumerate(zip(topics + opens, intents, strict=True)):
        params = {"cue": "apple_vinegar" if "りんご酢" in text else "banana"}
        result.append(
            Question(intent, text, f"eval:{i}", params if intent in {"why", "preference"} else {})
        )
    return result


def balanced_cases(size: int, first_seed: int) -> list[tuple[int, Question]]:
    cases: list[tuple[int, Question]] = []
    seed = first_seed
    while len(cases) < size:
        cases.extend((seed, q) for q in balanced_questions(seed)[: size - len(cases)])
        seed += 1
    if seed - first_seed > 1000:
        raise ValueError("balanced split needs too many worlds (keeps seed ranges disjoint)")
    return cases


async def export_dataset(
    out: Path,
    train_size: int = 4000,
    valid_size: int = 400,
    balanced: bool = False,
    companion: bool = False,
) -> dict[str, Any]:
    if not 1 <= train_size <= 98000 or not 1 <= valid_size <= 98000:
        raise ValueError("split sizes must be 1..98000 (keeps seed ranges disjoint)")
    out.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = {
        "version": 3 if companion else 1,
        "companion": companion,
        "balanced": balanced,
        "splits": {},
        "token_estimate_method": (
            "ASCII characters / 4 + non-ASCII characters * 1.5, including schemas"
        ),
    }
    for split, size, first_seed in (
        ("train", train_size, 1000),
        ("valid", valid_size, 2000),
        ("test", 0, 37),
    ):
        cases = []
        if split == "test":
            cases = [(37, q) for q in eval_questions() + questions(2)]
        elif balanced:
            cases = balanced_cases(size, first_seed)
        else:
            for index in range(size):
                seed = first_seed + index // 98
                cases.append((seed, questions(seed % 2)[index % 98]))
        if companion:
            if split == "test":
                cases.extend((37, q) for q in companion_questions(2))
            else:
                # Replace a regular fraction, retaining disjoint world/phrasing ranges.
                for index in range(0, len(cases), 5):
                    seed, _ = cases[index]
                    cases[index] = (seed, companion_questions(seed % 2)[(index // 5) % 4])
        counts: Counter[str] = Counter()
        lengths = []
        hashes = []
        with (
            (out / f"{split}.jsonl").open("w", encoding="utf-8", newline="\n") as chat,
            (out / f"{split}.meta.jsonl").open("w", encoding="utf-8", newline="\n") as meta,
        ):
            for seed, q in cases:
                example = (
                    await companion_trace(seed, q)
                    if q.intent in INTENTS
                    else await oracle_trace(seed, q)
                )
                line = json.dumps(example, ensure_ascii=False, separators=(",", ":"))
                digest = hashlib.sha256(line.encode()).hexdigest()
                chat.write(line + "\n")
                meta.write(
                    json.dumps(
                        {"seed": seed, "question": q.to_dict(), "sha256": digest},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                hashes.append(digest)
                counts[q.intent] += 1
                lengths.append(token_estimate(example))
        stats["splits"][split] = {
            "examples": len(cases),
            "intents": dict(sorted(counts.items())),
            "seeds": sorted({seed for seed, _ in cases}),
            "templates": sorted({q.template_id for _, q in cases}),
            "estimated_tokens_mean": round(sum(lengths) / len(lengths), 1),
            "estimated_tokens_max": max(lengths),
            "sha256": hashlib.sha256("".join(hashes).encode()).hexdigest(),
        }
    stats["max_length_estimate"] = max(s["estimated_tokens_max"] for s in stats["splits"].values())
    stats["max_length"] = math.ceil(stats["max_length_estimate"] / 128) * 128
    (out / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return stats
