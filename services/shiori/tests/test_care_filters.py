from __future__ import annotations

from datetime import UTC, datetime

from tsuyu_shiori.records import Record
from tsuyu_shiori.tools.filters import select_records


def test_filters_intersect_without_mutating_records() -> None:
    records = [
        Record("#1", "training", {"research_day": 2, "cue": "banana", "valence": "reward"}),
        Record("#2", "training", {"research_day": 2, "cue": "banana", "valence": "punish"}),
        Record("#3", "sleep", {"research_day": 2, "hours": 8}),
    ]
    assert (
        select_records(records, research_day=2, cue="banana", valence="reward", kinds=["training"])
        == records[:1]
    )
    assert select_records(records, kinds=["sleep"]) == records[2:]
    assert select_records(records, kinds=[]) == []
    assert select_records(records, research_day=3) == []
    assert len(records) == 3


def test_temporal_window_is_half_open_and_excludes_undated_records() -> None:
    records = [Record("#1", "meal", occurred_at=datetime(2026, 10, 1, tzinfo=UTC))]
    assert select_records(records, since="2026-10-01T00:00:00+00:00") == records
    assert select_records(records, until="2026-10-01T00:00:00+00:00") == []
    assert select_records([Record("#2", "meal")], since="2026-10-01T00:00:00+00:00") == []
