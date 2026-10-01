"""Filter host records after retrieval, without changing the RecordStore contract."""

from __future__ import annotations

from datetime import datetime

from tsuyu_shiori.records import Record


def select_records(
    records: list[Record],
    *,
    research_day: int | None = None,
    cue: str | None = None,
    valence: str | None = None,
    kinds: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[Record]:
    selected = []
    for record in records:
        if kinds is not None and record.kind not in kinds:
            continue
        if any(
            value is not None and record.data.get(key) != value
            for key, value in (("research_day", research_day), ("cue", cue), ("valence", valence))
        ):
            continue
        if since is not None or until is not None:
            if record.occurred_at is None:
                continue
            if since is not None and record.occurred_at < datetime.fromisoformat(since):
                continue
            if until is not None and record.occurred_at >= datetime.fromisoformat(until):
                continue
        selected.append(record)
    return selected
