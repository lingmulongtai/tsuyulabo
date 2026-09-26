from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tsuyulabo_api.domain.puzzles.common import VerifyResult, times_reason, verify_wall_clock


def test_timing_contract() -> None:
    assert times_reason([0, 0, 10], 10) is None
    assert times_reason([0, 0], 10, strict=True) == "non_monotonic_time"
    for times, elapsed in [([-1], 0), ([True], 10), ([2], 1), ([float("nan")], 10), ([], -1)]:
        assert times_reason(times, elapsed) == "non_monotonic_time"
    assert times_reason([11], 11, limit=10) == "time_exceeded"
    start = datetime(2026, 1, 1, tzinfo=UTC)
    assert verify_wall_clock(start, start + timedelta(seconds=8), 10000).valid
    assert not verify_wall_clock(start, start + timedelta(seconds=7.999), 10000).valid
    assert not verify_wall_clock(start, start + timedelta(minutes=10), 1).valid
    assert VerifyResult(False, "wrong_length").to_dict() == {
        "valid": False,
        "reason": "wrong_length",
    }
