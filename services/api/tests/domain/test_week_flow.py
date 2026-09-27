from __future__ import annotations

import ast
import sys
from datetime import datetime, timedelta
from pathlib import Path
from random import Random

from tsuyulabo_api.domain import (
    adults,
    care_miss,
    eclosion,
    friends,
    lifecycle,
    presentation,
    sleep,
    team,
)
from tsuyulabo_api.domain.clock import JST, research_day_start
from tsuyulabo_api.domain.events import CareEvent
from tsuyulabo_api.domain.stats import Stats, apply_cleaning, apply_meal, decay


def test_week_to_adult_team_flow() -> None:
    start = datetime(2026, 9, 27, 4, tzinfo=JST)
    log: list[CareEvent] = []
    state = Stats(start)
    for day in range(1, 8):
        for hour in (4, 12, 18):
            now = research_day_start(start, day).replace(hour=hour)
            state = decay(state, start, now)
            availability = {
                item.action: item for item in lifecycle.action_availability(start, now, log)
            }
            assert availability["meal"].status == "available"
            state = apply_meal(state)
            log.append(CareEvent(now, "meal", score=500))
            if day >= 2:
                assert availability["training"].status == "available"
                log.append(CareEvent(now, "training", stars=3))
            if hour == 4 and day in (2, 3, 4, 5):
                state = apply_cleaning(state, 100)
                log.append(CareEvent(now, "cleaning", score=100))
            if hour == 4 and day in (1, 6):
                log.append(CareEvent(now, "temperature", score=100))
            if day == 5 and hour == 18:
                log.append(CareEvent(now, "pupation_site", hit=True))
    now = research_day_start(start, 7).replace(hour=18)
    assert lifecycle.ready_to_eclose(start, now)
    misses = care_miss.evaluate(start, start, now, log)
    assert len(misses) == 1 and next(iter(misses))[0] == "hunger_zero"
    report = presentation.summarize(log, misses)
    assert (report.points, report.rank, report.shizuku, report.research_points) == (
        35600,
        "silver",
        5933,
        890,
    )
    adult = eclosion.roll(Random(1), report.rank, temperature_average=100, pupation_hit=True)
    member = team.gather(team.GatherState(now), now + timedelta(hours=8), Random(2), {"banana": 1})
    progress = adults.add_exp(adults.AdultProgress(adult.stars), member.pending_exp, Random(3))
    assert progress.level == 2
    result = sleep.wake(now, now + timedelta(hours=10), member.energy)
    assert result.shizuku == 200 and result.energy == 100
    assert friends.validate_code(friends.generate_code(Random(4)))
    # Eclosion may be delayed indefinitely without further care penalties.
    assert care_miss.evaluate(start, now, now + timedelta(days=14), log) == set()


def test_domain_has_only_standard_library_dependencies() -> None:
    root = Path(__file__).resolve().parents[2] / "src/tsuyulabo_api/domain"
    for source in root.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    alias.name.split(".")[0] in sys.stdlib_module_names for alias in node.names
                ), source
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert node.module and node.module.split(".")[0] in sys.stdlib_module_names, source
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"now", "utcnow", "today"}, source
