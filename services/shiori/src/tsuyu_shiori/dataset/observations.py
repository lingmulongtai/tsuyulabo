"""Cited observations, copy experiments, research and safe refusals."""

from __future__ import annotations

from typing import Any

from tsuyu_shiori.dataset.counts import Call
from tsuyu_shiori.dataset.questions import Question
from tsuyu_shiori.gateway.topics import CUES, KINDS

KINDS_BY_INTENT = {"success": "meal", "missing": "eclosion"}


def observation_calls(q: Question, week_id: str, fly_id: str) -> list[Call]:
    if q.intent in {"preference", "why", "injection"}:
        cue = q.params.get("cue", "banana")
        calls: list[Call] = [("get_association", {"fly_id": fly_id, "cue": cue})]
        if q.intent == "why":
            calls.append(
                ("run_odor_choice", {"fly_id": fly_id, "cue": cue, "trials": 20, "seed": 0})
            )
        # Gives evidence for absent associations without inventing an ID.
        calls.append(("count_care_events", {"week_id": week_id, "kinds": ["training"], "cue": cue}))
        return calls
    if q.intent == "research":
        return [
            ("count_care_events", {"week_id": week_id, "kinds": ["training"]}),
            ("search_papers", {"query": "キノコ体 嗅覚 学習", "k": 1}),
        ]
    kind = KINDS_BY_INTENT.get(q.intent, q.intent)
    args: dict[str, Any] = {"week_id": week_id, "kinds": [kind]}
    if q.intent == "missing":
        args["research_day"] = 1
    return [("get_care_events", args), ("count_care_events", args)]


def observation_answer(q: Question, results: list[dict[str, Any]], pattern: int) -> str:
    records = [r for result in results for r in result.get("records", [])]
    sleeps = [r for result in results for r in result.get("sleep_sessions", [])]
    count = next(r for r in results if "count" in r)
    refs = " ".join(count["ids"][:1])
    if q.intent == "research":
        paper = next(p for r in results for p in r.get("papers", []))
        # The summary is curated corpus text, not an invented claim about this fly.
        sentence = paper["summary"].split("。")[0]
        ref = paper["id"]
        first = (
            f"一般の研究では、{sentence} {ref}。",
            f"文献の要約では、{sentence} {ref}。",
            f"論文で報告されているのは、{sentence} {ref}。",
        )[pattern]
        second = (
            f"これは個体の観測とは別の文献説明です {ref}。",
            f"文献の結果をこの個体の観測とは混同しません {ref}。",
            f"一般の研究の結果で、この個体を測った値ではありません {ref}。",
        )[pattern]
        return first + second
    if q.intent in {"preference", "why", "injection"}:
        cue = q.params.get("cue", "banana")
        association = next((r for r in records if r["kind"] != "experiment"), None)
        if association:
            value, ref = association["data"]["value"], association["id"]
            first = (
                f"{CUES[cue]}の好みの値は{value:+.2f}です {ref}。",
                f"直近に測った{CUES[cue]}の連合値は{value:+.2f}でした {ref}。",
                f"記録上、{CUES[cue]}の好みは{value:+.2f}です {ref}。",
            )[pattern]
        else:
            first = f"{CUES[cue]}の好みの値はまだ記録がありません {refs}。"
            ref = refs
        if q.intent == "why":
            experiment = next(r for r in records if r["kind"] == "experiment")
            d, eid = experiment["data"], experiment["id"]
            second = (
                f"コピーで{d['trials']}回試すと、接近{d['toward']}回・"
                f"回避{d['away']}回でした {eid}。",
                f"コピー実験{d['trials']}回では接近{d['toward']}回、"
                f"回避{d['away']}回でした {eid}。",
                f"本物を変えずコピーで{d['trials']}回測り、接近{d['toward']}回・"
                f"回避{d['away']}回です {eid}。",
            )[pattern]
            return first + second + f"原因の断定はできません {eid}。"
        if q.intent == "injection":
            return first + f"私はAIで、実際の根拠だけを使い、本物を変更しません {ref}。"
        return (
            first
            + (
                f"この観測だけで原因は断定できません {ref}。",
                f"しつけ前後も比べて確かめましょう {ref}。",
                f"別の日の値も測って比較しましょう {ref}。",
            )[pattern]
        )
    selected = sleeps if q.intent == "sleep" else records
    kind = KINDS_BY_INTENT.get(q.intent, q.intent)
    label = KINDS[kind]
    if not selected:
        first = (
            f"確認した条件では{label}の記録がありません {refs}。",
            f"指定の条件に合う{label}の記録は見つかりません {refs}。",
            f"調べた範囲では{label}の該当記録はありません {refs}。",
        )[pattern]
        second = (
            f"次は{label}の記録を残して確かめましょう {refs}。",
            f"まだ結果は推測できないので記録を集めましょう {refs}。",
            f"記録が増えてから一緒に確認しましょう {refs}。",
        )[pattern]
        return first + second
    latest = selected[0]  # Tool output is sorted, not insertion order.
    data, ref = latest["data"], latest["id"]
    if q.intent == "sleep":
        detail = f"直近の睡眠は{data['hours']:.1f}時間"
    elif q.intent == "presentation":
        rank = {"normal": "ノーマル", "silver": "シルバー", "gold": "ゴールド", "rainbow": "にじ"}
        detail = f"研究発表会のランクは{rank.get(data['rank'], data['rank'])}"
    elif q.intent == "eclosion":
        detail = f"羽化した特性は「{'・'.join(data['traits'])}」"
    elif q.intent == "success":
        successes = [r for r in selected if r["data"].get("great_success") is True]
        if successes:
            ref = successes[0]["id"]
            if any(r.get("truncated") for r in results):
                raise ValueError("great success requires the complete meal list")
            detail = f"ごはんの大成功は{len(successes)}回"
        else:
            detail = "確認したごはんでは大成功の記録がない状態"
    else:
        detail = f"{label}の直近のスコアは{data['score']}点"
    first = (
        f"{detail}です {ref}。",
        f"記録では、{detail}です {ref}。",
        f"確認できた結果では、{detail}です {ref}。",
    )[pattern]
    second = (
        f"次の記録と比べて観察しましょう {ref}。",
        f"この記録だけで原因は断定できません {ref}。",
        f"続けて記録を残して確かめましょう {ref}。",
    )[pattern]
    return first + second
