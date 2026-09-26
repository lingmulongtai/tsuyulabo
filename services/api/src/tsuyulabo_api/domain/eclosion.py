from __future__ import annotations

from dataclasses import dataclass
from random import Random

from . import constants as c


def odds(
    rank: str, temperature_average: float = 0, pupation_hit: bool = False
) -> tuple[float, ...]:
    if rank not in c.ODDS:
        raise ValueError("unknown rank")
    weights = list(c.ODDS[rank])
    if temperature_average >= c.TEMPERATURE_BONUS_THRESHOLD:
        weights[0] -= c.TEMPERATURE_ODDS_SHIFT
        weights[1] += c.TEMPERATURE_ODDS_SHIFT
    if pupation_hit:
        weights[0] -= c.SITE_ODDS_SHIFT
        weights[2] += c.SITE_ODDS_SHIFT
    return tuple(weights)


def roll_tier(
    rng: Random, rank: str, temperature_average: float = 0, pupation_hit: bool = False
) -> int:
    return rng.choices(
        range(len(c.TIER_COLORS)), weights=odds(rank, temperature_average, pupation_hit)
    )[0]


def roll_traits(rng: Random) -> tuple[str, str]:
    # Rejection sampling keeps all allowed unordered pairs equally likely.
    while True:
        first, second = rng.sample(tuple(c.TRAITS), c.TRAIT_COUNT)
        if frozenset((first, second)) not in c.EXCLUSIVE_TRAITS:
            return first, second


def omen_sequence(rng: Random, tier: int) -> tuple[int, ...]:
    if not 0 <= tier < len(c.TIER_COLORS):
        raise ValueError("unknown tier")
    sequence = list(range(tier + 1))
    # The optional fake-out can only show an existing color; rainbow has no tier+1.
    if 2 <= tier < len(c.TIER_COLORS) - 1 and rng.random() < c.FAKE_OUT_CHANCE:
        sequence.extend((tier + 1, tier))
    return tuple(sequence)


@dataclass(frozen=True)
class AdultRoll:
    tier: int
    stars: int
    strain: str
    sex: str
    traits: tuple[str, str]
    omen_sequence: tuple[int, ...]


def roll(
    rng: Random, rank: str, temperature_average: float = 0, pupation_hit: bool = False
) -> AdultRoll:
    tier = roll_tier(rng, rank, temperature_average, pupation_hit)
    stars = rng.choice((1, 2)) if tier == 0 else tier + 2
    strain = rng.choice(c.MUTATIONS) if tier == 3 else c.WILD_STRAIN
    sex = rng.choice(c.SEXES)
    traits = roll_traits(rng)
    return AdultRoll(tier, stars, strain, sex, traits, omen_sequence(rng, tier))
