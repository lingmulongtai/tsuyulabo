from __future__ import annotations

from datetime import datetime, timedelta

from tsuyulabo_api.domain import contest
from tsuyulabo_api.domain.clock import JST


def test_week_phases_and_tie_break() -> None:
    monday = datetime(2026, 1, 5, tzinfo=JST)
    week, entry_close, vote_close, theme = contest.week_at(monday)
    assert week == "2026-W02"
    assert theme == "バナナ祭り"
    assert contest.phase(entry_close - timedelta(seconds=1), entry_close, vote_close) == "entry"
    assert contest.phase(entry_close, entry_close, vote_close) == "vote"
    assert contest.phase(vote_close, entry_close, vote_close) == "results"
    assert contest.rank_entries(
        [
            ("later", 2, monday + timedelta(seconds=1)),
            ("first", 2, monday),
            ("low", 1, monday),
        ]
    ) == ["first", "later", "low"]


def test_layout_types_are_fixed() -> None:
    layout = dict.fromkeys(contest.SLOTS)
    assert contest.valid_layout(layout | {"left": "flower_ornament"})
    assert not contest.valid_layout(layout | {"left": "leaf_hat"})
    assert not contest.valid_layout(layout | {"extra": None})
