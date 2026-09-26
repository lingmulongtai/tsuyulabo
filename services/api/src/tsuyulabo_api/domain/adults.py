from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from random import Random

from . import constants as c


def level_cap(stars: int) -> int:
    if type(stars) is not int or stars not in c.LEVEL_CAPS:
        raise ValueError("stars must be between 1 and 5")
    return c.LEVEL_CAPS[stars]


def _validate_level(level: int) -> None:
    if type(level) is not int or not 1 <= level <= max(c.LEVEL_CAPS.values()):
        raise ValueError("invalid level")


def level_up_cost(level: int) -> int:
    _validate_level(level)
    return c.LEVEL_COST_FACTOR * level


def exp_threshold(level: int) -> int:
    _validate_level(level)
    return c.EXP_FACTOR * level


def unlock_subskills(rng: Random, level: int, prior: Mapping[int, str]) -> dict[int, str]:
    """Persist returned rolls. Independent uniform draws may repeat across slots."""
    _validate_level(level)
    if any(
        slot not in c.SUBSKILL_LEVELS or slot > level or skill not in c.SUBSKILLS
        for slot, skill in prior.items()
    ):
        raise ValueError("invalid prior subskills")
    result = dict(prior)
    for slot in c.SUBSKILL_LEVELS:
        if slot <= level and slot not in result:
            result[slot] = rng.choice(tuple(c.SUBSKILLS))
    return result


@dataclass(frozen=True)
class AdultProgress:
    stars: int
    level: int = 1
    exp: int = 0
    subskills: tuple[tuple[int, str], ...] = ()


def _validate(state: AdultProgress) -> None:
    if not 1 <= state.level <= level_cap(state.stars) or state.exp < 0:
        raise ValueError("invalid adult progression")


def add_exp(state: AdultProgress, amount: int, rng: Random) -> AdultProgress:
    _validate(state)
    if type(amount) is not int or amount < 0:
        raise ValueError("experience must be a nonnegative integer")
    level, exp, cap = state.level, state.exp + amount, level_cap(state.stars)
    while level < cap and exp >= exp_threshold(level):
        exp -= exp_threshold(level)
        level += 1
    skills = unlock_subskills(rng, level, dict(state.subskills))
    return AdultProgress(state.stars, level, 0 if level == cap else exp, tuple(skills.items()))


def level_up(state: AdultProgress, shizuku: int, rng: Random) -> tuple[AdultProgress, int]:
    _validate(state)
    if state.level == level_cap(state.stars):
        raise ValueError("level cap reached")
    cost = level_up_cost(state.level)
    if shizuku < cost:
        raise ValueError("insufficient shizuku")
    level = state.level + 1
    skills = unlock_subskills(rng, level, dict(state.subskills))
    return replace(
        state,
        level=level,
        exp=0 if level == level_cap(state.stars) else state.exp,
        subskills=tuple(skills.items()),
    ), cost


def bonuses(subskills: Iterable[str]) -> dict[str, float]:
    result = {
        "gather_bonus": 0.0,
        "great_bonus": 0.0,
        "drop_bonus": 0.0,
        "bag_bonus": 0.0,
        "energy_bonus": 0.0,
        "rp_bonus": 0.0,
    }
    keys = {
        "gather_s": "gather_bonus",
        "gather_m": "gather_bonus",
        "great_up": "great_bonus",
        "drop_bonus": "drop_bonus",
        "bag_up": "bag_bonus",
        "energy_up": "energy_bonus",
        "rp_up": "rp_bonus",
    }
    for skill in subskills:
        if skill not in c.SUBSKILLS:
            raise ValueError("unknown subskill")
        result[keys[skill]] += c.SUBSKILLS[skill][1]
    result["great_bonus"] = min(c.TEAM_GREAT_BONUS_CAP, result["great_bonus"])
    return result
