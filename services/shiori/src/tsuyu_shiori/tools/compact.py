"""Bounded care views; keep only observation fields, never opaque host payloads."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC
from typing import Any

from tsuyu_shiori.records import Record

LIMIT = 20
FIELDS = ("cue", "valence", "value", "score", "great_success", "traits", "rank", "hours")


def newest_records(records: list[Record]) -> list[Record]:
    def key(record: Record) -> tuple[float, int]:
        at = record.occurred_at
        if at is not None and at.tzinfo is None:
            at = at.replace(tzinfo=UTC)
        seq = record.id.removeprefix("#")
        return (at.timestamp() if at else float("-inf"), int(seq) if seq.isdigit() else 0)

    return sorted(reversed(records), key=key, reverse=True)


def compact_record(record: Record) -> dict[str, Any]:
    result = {
        "id": record.id,
        "kind": record.kind,
        "research_day": record.data.get("research_day"),
        "data": {key: deepcopy(record.data[key]) for key in FIELDS if key in record.data},
    }
    if record.occurred_at is not None:
        result["occurred_at"] = record.occurred_at.isoformat()
    return result


def compact_result(care: list[Record], sleeps: list[Record]) -> dict[str, Any]:
    # A single shared cap also bounds weeks containing many sleep sessions.
    selected = newest_records(care + sleeps)[:LIMIT]
    return {
        "records": [compact_record(r) for r in selected if r.kind != "sleep"],
        "sleep_sessions": [compact_record(r) for r in selected if r.kind == "sleep"],
        "total": len(care) + len(sleeps),
        "truncated": len(care) + len(sleeps) > LIMIT,
    }
