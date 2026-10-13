from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from tsuyu_shiori.hint_rules import detect_trouble

NOW = datetime(2026, 10, 13, tzinfo=UTC)


@pytest.mark.parametrize(
    ("state", "kind"),
    [
        ({"temperature": 30}, "hot"),
        ({"temperature": 17}, "cold"),
        ({"food": {"moisture": 0.2}}, "dry"),
        ({"mould": 0.3}, "mould"),
        ({"fed_at": (NOW - timedelta(hours=13)).isoformat()}, "meal"),
        ({"behaviour": "escape"}, "stress"),
    ],
)
def test_rules_use_measured_state(state, kind):
    assert detect_trouble(state, NOW).kind == kind


@pytest.mark.parametrize(
    "state", [{}, {"temperature": float("nan")}, {"fed_at": "invalid"}, {"temperature": 25}]
)
def test_missing_or_healthy_state_stays_quiet(state):
    assert detect_trouble(state, NOW) is None
