from __future__ import annotations

from datetime import datetime, timedelta

from tsuyulabo_api.domain.care_miss import default_pupation_choice, evaluate
from tsuyulabo_api.domain.clock import JST, research_day_start
from tsuyulabo_api.domain.events import CareEvent

START = datetime(2026, 9, 27, 8, tzinfo=JST)


def test_full_week_idempotency_and_deadlines() -> None:
    end = research_day_start(START, 8)
    misses = evaluate(START, START, end, [])
    assert len(misses) == 20  # 12 meals, 4 cleanings, 2 temperatures, site, starvation.
    assert misses | evaluate(START, START, end, []) == misses
    assert evaluate(START, end, research_day_start(START, 30), []) == set()
    middle = research_day_start(START, 4)
    assert evaluate(START, START, middle, []) | evaluate(START, middle, end, []) == misses
    boundary = research_day_start(START, 2).replace(hour=12)
    assert ("meal", 2, "morning") not in evaluate(START, START, boundary - timedelta(seconds=1), [])
    assert ("meal", 2, "morning") in evaluate(START, START, boundary, [])


def test_events_and_three_hours_zero() -> None:
    events = [CareEvent(START, "temperature")]
    for day in range(1, 6):
        for hour in (4, 12, 18):
            at = research_day_start(START, day).replace(hour=hour)
            if at >= START:
                events.append(CareEvent(at, "meal", great_success=True))
        if day > 1:
            events.append(CareEvent(research_day_start(START, day), "cleaning", score=100))
    events += [
        CareEvent(research_day_start(START, 5).replace(hour=18), "pupation_site"),
        CareEvent(research_day_start(START, 6), "temperature"),
    ]
    misses = evaluate(START, START, research_day_start(START, 8), events)
    assert all(key[0] == "hunger_zero" for key in misses)
    assert len(misses) == 1  # Even great meals cannot bridge the ten-hour night.
    hatch = START.replace(hour=18)
    fed = [CareEvent(hatch + timedelta(hours=7.79), "meal")]
    assert not any(
        k[0] == "hunger_zero" for k in evaluate(START, START, hatch + timedelta(hours=8), fed)
    )
    assert default_pupation_choice([{"id": "c"}, {"id": "a"}, {"id": "b"}]) == "a"
