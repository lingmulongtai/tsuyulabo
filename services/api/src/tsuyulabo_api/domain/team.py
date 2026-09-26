"""Piecewise integration preserves fractional gathering across lazy reads."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from math import floor, isfinite
from random import Random

from . import constants as c
from .adults import bonuses
from .clock import local


def energy_factor(energy: float) -> float:
    if not isfinite(energy) or not 0 <= energy <= c.STAT_MAX:
        raise ValueError("energy must be in [0, 100]")
    return next(factor for threshold, factor in c.ENERGY_FACTORS if energy >= threshold)


def material_weights(preferences: Mapping[str, float]) -> dict[str, float]:
    weights = dict.fromkeys(c.MATERIALS, 1.0)
    for cue, material in c.CUE_MATERIALS.items():
        value = preferences.get(cue, 0.0)
        if not isfinite(value) or not -1 <= value <= 1:
            raise ValueError("preference must be in [-1, 1]")
        weights[material] += c.PREFERENCE_WEIGHT * max(0.0, value)
    return weights


def items_per_hour(level: int, energy: float, gather_bonus: float = 0) -> float:
    return (c.GATHER_BASE + c.GATHER_PER_LEVEL * level) * energy_factor(energy) * (1 + gather_bonus)


@dataclass(frozen=True)
class GatherState:
    last_computed_at: datetime
    level: int = 1
    energy: float = c.STAT_MAX
    bag: tuple[str, ...] = ()
    item_progress: float = 0.0
    shizuku: float = 0.0
    pending_exp: int = 0


def gather(
    state: GatherState,
    now: datetime,
    rng: Random,
    preferences: Mapping[str, float],
    subskills: Iterable[str] = (),
) -> GatherState:
    """Gather until the bag fills; energy still decays over the entire interval.

    Rare jelly replaces a material in an item slot and grants the same one exp.
    Shizuku accrues while gathering is active (including fractional items).
    The caller stores rng state and awards pending_exp via adults.add_exp.
    """
    hours = (local(now) - local(state.last_computed_at)).total_seconds() / 3600
    bonus = bonuses(subskills)
    cap = c.BAG_CAPACITY + int(bonus["bag_bonus"])
    if hours < 0 or not 1 <= state.level <= max(c.LEVEL_CAPS.values()):
        raise ValueError("invalid gathering interval or level")
    energy_factor(state.energy)
    if (
        not isfinite(state.item_progress)
        or not 0 <= state.item_progress < 1
        or len(state.bag) > cap
        or not isfinite(state.shizuku)
        or state.shizuku < 0
    ):
        raise ValueError("invalid bag state")
    weights = material_weights(preferences)
    # Split at the two energy thresholds, using a midpoint to handle exact boundaries.
    cuts = sorted(
        {
            0.0,
            hours,
            *[
                (state.energy - threshold) / c.ENERGY_DECAY
                for threshold, _ in c.ENERGY_FACTORS
                if threshold > 0 and 0 < (state.energy - threshold) / c.ENERGY_DECAY < hours
            ],
        }
    )
    progress = state.item_progress
    bag = list(state.bag)
    shizuku, exp = state.shizuku, state.pending_exp
    for begin, end in zip(cuts, cuts[1:], strict=False):
        if len(bag) >= cap:
            progress = 0.0
            break
        midpoint_energy = max(0.0, state.energy - (begin + end) / 2 * c.ENERGY_DECAY)
        rate = items_per_hour(state.level, midpoint_energy, bonus["gather_bonus"])
        active_hours = min(end - begin, (cap - len(bag) - progress) / rate)
        amount = progress + active_hours * rate
        # The epsilon only removes accumulated binary floating point boundary error.
        count = min(cap - len(bag), floor(amount + 1e-10))
        progress = max(0.0, amount - count)
        shizuku += (
            active_hours
            * (c.SHIZUKU_BASE + c.SHIZUKU_PER_LEVEL * state.level)
            * (1 + bonus["drop_bonus"])
        )
        for _ in range(count):
            item = (
                c.RARE_DROP
                if rng.random() < c.RARE_DROP_CHANCE
                else rng.choices(tuple(weights), weights=tuple(weights.values()))[0]
            )
            bag.append(item)
        exp += count * c.ITEM_EXP
        if len(bag) == cap:
            progress = 0.0
    return GatherState(
        local(now),
        state.level,
        max(0.0, state.energy - hours * c.ENERGY_DECAY),
        tuple(bag),
        progress,
        shizuku,
        exp,
    )
