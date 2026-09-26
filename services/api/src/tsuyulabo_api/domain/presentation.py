from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import floor

from . import constants as c
from .care_miss import MissKey
from .events import CareEvent


@dataclass(frozen=True)
class Presentation:
    meal_points: int
    training_points: int
    care_points: int
    care_miss: int
    penalty: int
    points: int
    rank: str
    shizuku: int
    research_points: int


def rank_for(points: int) -> str:
    return next(
        (rank for rank, threshold in reversed(c.RANK_THRESHOLDS.items()) if points >= threshold),
        "normal",
    )


def rewards(points: int, rp_bonus: float = 0) -> tuple[int, int]:
    """Apply the spec's floor formulas, including negative totals (no unstated clamp)."""
    if rp_bonus < 0:
        raise ValueError("bonus must be nonnegative")
    return (
        floor(points / c.PRESENTATION_SHIZUKU_DIVISOR),
        floor(points / c.PRESENTATION_RP_DIVISOR * (1 + rp_bonus)),
    )


def summarize(
    events: Iterable[CareEvent], miss_keys: Iterable[MissKey] = (), rp_bonus: float = 0
) -> Presentation:
    meal = training = care = 0
    for event in events:
        if event.kind == "meal":
            meal += event.score + event.great_success * c.GREAT_POINTS
        elif event.kind == "training":
            training += event.stars * c.TRAINING_STAR_POINTS + event.hirameki * c.HIRAMEKI_POINTS
        elif event.kind in ("cleaning", "temperature"):
            care += event.score * c.CARE_SCORE_POINTS
        elif event.kind == "pupation_site":
            care += event.hit * c.SITE_HIT_POINTS
    count = len(set(miss_keys))
    penalty = count * c.CARE_MISS_PENALTY
    points = meal + training + care - penalty
    shizuku, rp = rewards(points, rp_bonus)
    return Presentation(meal, training, care, count, penalty, points, rank_for(points), shizuku, rp)
