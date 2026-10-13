from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from tsuyu_shiori.diary_events import notable_events
from tsuyu_shiori.records import Record

START = datetime(2026, 10, 12, tzinfo=UTC)


def record(seq, kind, data, offset=0):
    return Record(f"#{seq:04}", kind, data, "w", "f", START + timedelta(hours=offset))


def test_first_flight_uses_lifetime_history_and_excludes_future():
    records = [
        record(1, "behaviour", {"behaviour": "fly"}, -2),
        record(2, "behaviour", {"behaviour": "fly"}, 1),
        record(3, "eclosion", {}, 25),
    ]
    result = notable_events(records, START, START + timedelta(days=1))
    assert [m.kind for m in result] == ["behaviour"]


def test_trained_approach_requires_earlier_training_and_preserves_snapshot():
    records = [
        record(1, "training", {"cue": "banana", "valence": "reward"}, -1),
        record(2, "behaviour", {"behaviour": "approach", "cue": "banana", "stage": "adult"}, 1),
    ]
    result = notable_events(records, START, START + timedelta(days=1))
    assert result[0].kind == "trained_approach"
    assert result[0].evidence == ["#0002", "#0001"]
    assert result[0].snapshot["stage"] == "adult"
    assert "growth" not in [m.kind for m in result]


def test_undated_records_do_not_become_daily_observations():
    assert (
        notable_events([Record("#0001", "meal", {}, "w")], START, START + timedelta(days=1)) == []
    )
    with pytest.raises(ValueError):
        notable_events([], START.replace(tzinfo=None), START)


def test_pending_training_never_invents_punishment_or_prior_learning():
    records = [
        record(1, "training", {"learning_status": "pending"}),
        record(2, "behaviour", {"behaviour": "approach", "cue": "banana"}, 1),
    ]
    result = notable_events(records, START, START + timedelta(days=1))
    assert all("苦い" not in moment.description for moment in result)
    assert "trained_approach" not in {moment.kind for moment in result}
