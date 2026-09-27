from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import inf

import pytest
from tsuyulabo_api.domain.circadian import Circadian, SleepRecord, clock_statistics, summarize
from tsuyulabo_api.domain.clock import JST
from tsuyulabo_api.domain.sleep import energy_recovery, wake

BASE = datetime(2026, 1, 1, 23, tzinfo=JST)


def records(count: int = 7, hours: float = 8) -> list[SleepRecord]:
    return [
        SleepRecord(BASE + timedelta(days=i), BASE + timedelta(days=i, hours=hours))
        for i in range(count)
    ]


def test_empty_and_incomplete_history() -> None:
    assert summarize([], BASE) == Circadian()
    invalid = [SleepRecord(BASE, None), SleepRecord(BASE, BASE - timedelta(hours=1))]
    assert summarize(invalid + records(), BASE) == Circadian()


@pytest.mark.parametrize("count, gauge", [(1, 14), (2, 29), (6, 86), (7, 100)])
def test_regular_nights_accumulate(count: int, gauge: int) -> None:
    history = records(count)
    result = summarize(history, history[-1].ended_at)
    assert result == Circadian(gauge, count, "23:00", "07:00")


def test_midnight_wraparound_for_both_times() -> None:
    times = [BASE.replace(hour=23, minute=55), BASE.replace(hour=0, minute=5)]
    spread, typical = clock_statistics(times)
    assert spread == pytest.approx(5, abs=0.001)
    assert typical == "00:00"
    history = [SleepRecord(t, t + timedelta(hours=8)) for t in times]
    result = summarize(history, BASE + timedelta(days=2))
    assert result.typical_bedtime == "00:00"
    assert result.typical_wake == "08:00"
    assert result.gauge == 28


def test_undefined_mean_and_wide_spread() -> None:
    opposite = [BASE, BASE + timedelta(hours=12)]
    assert clock_statistics(opposite) == (inf, None)
    assert clock_statistics([]) == (inf, None)
    history = [SleepRecord(t, t + timedelta(hours=8)) for t in opposite]
    result = summarize(history, BASE + timedelta(days=2))
    assert result.gauge == 9  # Only the duration portion remains.
    assert result.typical_bedtime is None and result.typical_wake is None


@pytest.mark.parametrize("hours, gauge", [(5.999, 70), (6, 100), (9, 100), (9.001, 70), (32, 70)])
def test_duration_uses_uncapped_hours_and_inclusive_bounds(hours: float, gauge: int) -> None:
    history = records(hours=hours)
    assert summarize(history, history[-1].ended_at).gauge == gauge


def test_latest_seven_sorted_and_future_ignored() -> None:
    history = records()
    now = history[-1].ended_at
    extra = [SleepRecord(BASE - timedelta(days=1, hours=5), BASE - timedelta(days=1))]
    extra += [SleepRecord(now, now + timedelta(hours=8)), SleepRecord(now, None)]
    assert summarize(reversed(extra + history), now) == summarize(history, now)


def test_streak_gap_bad_duration_and_staleness() -> None:
    history = records()
    now = history[-1].ended_at
    assert summarize(history[:3] + history[4:], now).streak == 3
    bad = SleepRecord(history[4].started_at, history[4].started_at + timedelta(hours=5))
    assert summarize(history[:4] + [bad] + history[5:], now).streak == 2
    assert summarize(history, now + timedelta(days=1)).streak == 7
    stale = summarize(history, now + timedelta(days=2))
    assert stale.streak == 0 and stale.gauge == 100


def test_streak_uses_sleep_game_day_across_midnight() -> None:
    starts = [BASE, BASE + timedelta(days=1, hours=2)]
    history = [SleepRecord(t, t + timedelta(hours=6)) for t in starts]
    assert summarize(history, history[-1].ended_at).streak == 2


def test_timezone_conversion_and_naive_rejection() -> None:
    history = records()
    utc = [SleepRecord(r.started_at.astimezone(UTC), r.ended_at.astimezone(UTC)) for r in history]
    assert summarize(utc, utc[-1].ended_at) == summarize(history, history[-1].ended_at)
    with pytest.raises(ValueError, match="timezone-aware"):
        summarize([], datetime(2026, 1, 1))


def test_wake_effects_threshold_and_caps() -> None:
    assert Circadian(79).shizuku_bonus == 0
    assert Circadian(80).shizuku_bonus == 20
    assert Circadian().energy_multiplier == 1
    assert Circadian(100).energy_multiplier == 1.3
    assert energy_recovery(2, 0.2, 1.3) == pytest.approx(46.8)
    assert energy_recovery(10, 0.2, 1.3) == 100
    result = wake(BASE.replace(hour=3), BASE.replace(hour=5), 80, 0.2, 1.3)
    assert result.energy == 100
    with pytest.raises(ValueError, match="multiplier"):
        energy_recovery(2, circadian_multiplier=1.4)
