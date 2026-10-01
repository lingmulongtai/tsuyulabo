"""Exact count oracle; never count a truncated record list."""

from __future__ import annotations

from typing import Any

from tsuyu_shiori.dataset.questions import Question
from tsuyu_shiori.gateway.topics import CUES

Call = tuple[str, dict[str, Any]]


def count_calls(question: Question, week_id: str) -> list[Call]:
    params = question.params
    if question.intent == "maximum":
        return [
            ("count_care_events", {"week_id": week_id, "kinds": ["training"], "cue": cue})
            for cue in CUES
        ]
    arguments: dict[str, Any] = {"week_id": week_id, "kinds": ["training"]}
    if "day" in params:
        # These worlds start Monday, so weekday and research day are equivalent.
        arguments["research_day"] = params["day"]
    for key in ("cue", "valence"):
        if key in params:
            arguments[key] = params[key]
    return [("count_care_events", arguments)]


def count_answer(question: Question, results: list[dict[str, Any]], pattern: int) -> str:
    result = max(results, key=lambda r: r["count"]) if question.intent == "maximum" else results[0]
    refs = " ".join(result["ids"][:2])
    n = result["count"]
    if question.intent == "maximum":
        label = CUES[result["filters"]["cue"]]
        first = (
            f"しつけを比べると{label}が最多で{n}回です {refs}。",
            f"刺激別の最多は{label}の{n}回でした {refs}。",
            f"今週は{label}のしつけが最多の{n}回です {refs}。",
        )[pattern]
    else:
        first = (
            f"該当する記録は{n}回です {refs}。",
            f"指定された条件のしつけは{n}回でした {refs}。",
            f"記録を集計すると、該当件数は{n}回です {refs}。",
        )[pattern]
    second = (
        f"確認できた記録の範囲での集計です {refs}。",
        f"この回数はツールが記録から集計した値です {refs}。",
        f"記録外の行動までは分かりません {refs}。",
    )[pattern]
    return first + second
