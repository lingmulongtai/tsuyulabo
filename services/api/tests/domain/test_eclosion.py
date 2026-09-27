from __future__ import annotations

from collections import Counter
from random import Random

import pytest
from tsuyulabo_api.domain import genetics
from tsuyulabo_api.domain.constants import EXCLUSIVE_TRAITS, ODDS
from tsuyulabo_api.domain.eclosion import odds, omen_sequence, roll, roll_tier


@pytest.mark.parametrize("rank", ODDS)
@pytest.mark.parametrize("temp,hit", [(0, False), (80, False), (79.999, True), (100, True)])
def test_adjusted_odds(rank: str, temp: float, hit: bool) -> None:
    weights = odds(rank, temp, hit)
    assert sum(weights) == 100 and min(weights) >= 0
    assert weights[0] == ODDS[rank][0] - (3 if temp >= 80 else 0) - (2 if hit else 0)


@pytest.mark.parametrize("rank", ODDS)
def test_ten_thousand_tiers(rank: str) -> None:
    rng = Random(123)
    counts = Counter(roll_tier(rng, rank) for _ in range(10000))
    for tier, percent in enumerate(ODDS[rank]):
        expected = percent * 100
        assert abs(counts[tier] - expected) < 6 * (expected * (1 - percent / 100)) ** 0.5


def test_outcomes_and_determinism() -> None:
    rng = Random(234)
    sexes: Counter = Counter()
    mutations: Counter = Counter()
    low_stars: Counter = Counter()
    for _ in range(10000):
        adult = roll(rng, "rainbow", 100, True)
        sexes[adult.sex] += 1
        assert frozenset(adult.traits) not in EXCLUSIVE_TRAITS
        assert len(set(adult.traits)) == 2
        assert adult.omen_sequence[-1] == adult.tier
        if adult.tier == 0:
            low_stars[adult.stars] += 1
        if adult.tier == 3:
            assert adult.stars == 5 and adult.mutation is not None
            mutations[adult.mutation["locus"]] += 1
        else:
            assert adult.strain == "wild"
    assert 4800 < sexes["m"] < 5200
    assert abs(low_stars[1] - low_stars[2]) < 150
    assert len(mutations) == 5 and min(mutations.values()) > 130
    assert roll(Random(99), "gold") == roll(Random(99), "gold")
    assert omen_sequence(Random(1), 2) == (0, 1, 2, 3, 2)
    assert omen_sequence(Random(1), 3) == (0, 1, 2, 3)


def test_inherited_phenotype_and_sex_survive_non_rainbow_eclosion() -> None:
    egg = genetics.wild_type("m")
    egg["w"] = ["w"]
    for seed in range(100):
        adult = roll(Random(seed), "normal", genotype=egg)
        assert adult.sex == "m" and adult.strain == "white"
        if adult.tier != 3:
            assert adult.genotype == egg and adult.mutation is None
    assert egg["w"] == ["w"]
