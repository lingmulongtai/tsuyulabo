"""Select notable, dated observations without inferring unrecorded milestones."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from tsuyu_shiori.records import Record


@dataclass(frozen=True)
class Moment:
    kind: str
    description: str
    evidence: list[str]
    snapshot: dict[str, Any]


def notable_events(records: list[Record], start: datetime, end: datetime) -> list[Moment]:
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError("a nonempty aware time window is required")
    ordered = sorted(
        (r for r in records if r.occurred_at is not None and r.occurred_at < end),
        key=lambda r: (r.occurred_at, r.id),
    )
    seen_flight = False
    trained: dict[str, Record] = {}
    moments = []
    for record in ordered:
        data = record.data
        action = data.get("behaviour")
        kind, description = "care", ""
        refs = [record.id]
        if record.kind == "training":
            kind, description = "training", "しつけの練習をしました"
            if data.get("valence") == "reward":
                description = "匂いとごほうびを結びつけるしつけをしました"
            elif data.get("valence") == "punish":
                description = "匂いと苦いものを結びつけるしつけをしました"
            if data.get("cue") and data.get("valence") in {"reward", "punish"}:
                trained[data["cue"]] = record
        elif record.kind == "behaviour":
            if action == "fly" and not seen_flight:
                kind, description = "first_flight", "初めて飛ぶ動きが脳の出力に記録されました"
            elif action == "approach" and data.get("cue") == "banana" and "banana" in trained:
                kind, description = (
                    "trained_approach",
                    "しつけのあと、バナナに寄る動きが脳の出力に記録されました",
                )
                refs.append(trained["banana"].id)
            elif action in {"avoid", "escape"} and data.get("stimulus") == "mould":
                kind, description = "mould_avoidance", "カビから離れる動きが記録されました"
            elif action:
                kind, description = "behaviour", "この子の動きが脳の出力に記録されました"
            seen_flight = seen_flight or action == "fly"
            if data.get("source") == "copy_odor_choice":
                description = description.replace("脳の出力", "コピーの出力")
                if data.get("experiment_evidence"):
                    refs.append(data["experiment_evidence"])
        elif record.kind == "eclosion":
            kind, description = "eclosion", "この子が羽化しました"
        elif record.kind == "meal":
            kind, description = "meal", "ごはんを入れました"
            if data.get("great_success") is True:
                description = "よくできたごはんを入れました"
            if data.get("growth_delta", 0) > 0:
                kind, description = "growth", "ごはんのあとに成長が記録されました"
        elif record.kind == "cleaning":
            description = "びんをそうじしました"
        if record.occurred_at < start or not description:
            continue
        moments.append(
            Moment(
                kind,
                description,
                refs,
                {
                    "record_id": record.id,
                    "at": record.occurred_at.isoformat(),
                    "stage": data.get("stage", "adult" if record.kind == "eclosion" else "egg"),
                    "behaviour": action or "rest",
                    "environment": data.get("environment", {}),
                    "seed": record.fly_id or record.week_id,
                    "sex": data.get("sex"),
                    "phenotypes": data.get("phenotypes", []),
                },
            )
        )
    priorities = {
        "eclosion": 0,
        "first_flight": 1,
        "trained_approach": 2,
        "mould_avoidance": 3,
        "growth": 4,
        "behaviour": 5,
    }
    return sorted(moments, key=lambda m: priorities.get(m.kind, 6))[:3]
