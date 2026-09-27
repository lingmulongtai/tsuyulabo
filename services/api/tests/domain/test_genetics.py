from __future__ import annotations

from collections import Counter
from copy import deepcopy
from random import Random

import pytest
from tsuyulabo_api.domain import genetics as g


@pytest.mark.parametrize("locus", ("w", "y"))
def test_x_linked_mutant_mother_and_wild_father(locus: str) -> None:
    mother, father = g.wild_type("f"), g.wild_type("m")
    mother[locus] = [locus, locus]
    rng = Random(1)
    sexes = Counter()
    for _ in range(1000):
        child = g.breed(rng, mother, father).genotype
        sexes[child["sex"]] += 1
        assert child[locus] == ([locus] if child["sex"] == "m" else [locus, "+"])
        assert g.phenotypes(child) == ([g.TRAITS[locus]] if child["sex"] == "m" else ["wild"])
    assert 450 < sexes["m"] < 550


def test_x_linked_mutant_father_never_passes_x_to_sons() -> None:
    mother, father = g.wild_type("f"), g.wild_type("m")
    father["w"] = ["w"]
    rng = Random(5)
    for _ in range(500):
        child = g.breed(rng, mother, father).genotype
        assert child["w"] == (["+"] if child["sex"] == "m" else ["+", "w"])
        assert g.phenotypes(child) == ["wild"]


@pytest.mark.parametrize("locus", ("e", "vg"))
def test_autosomal_carrier_cross(locus: str) -> None:
    mother, father = g.wild_type("f"), g.wild_type("m")
    mother[locus] = father[locus] = [locus, "+"]
    rng = Random(7)
    affected = sum(
        g.TRAITS[locus] in g.phenotypes(g.breed(rng, mother, father).genotype) for _ in range(10000)
    )
    assert 2350 < affected < 2650


def test_curly_survivors_and_recorded_lethality() -> None:
    mother, father = g.wild_type("f"), g.wild_type("m")
    mother["Cy"] = father["Cy"] = ["Cy", "+"]
    before = deepcopy((mother, father))
    rng = Random(9)
    children = [g.breed(rng, mother, father) for _ in range(10000)]
    assert all(not g.lethal(child.genotype) for child in children)
    assert 6500 < sum("curly" in g.phenotypes(c.genotype) for c in children) < 6850
    assert 3100 < sum(c.lethal_redraws for c in children) < 3600
    assert (mother, father) == before
    assert g.breed(Random(9), mother, father) == g.breed(Random(9), mother, father)


def test_normal_eggs_are_wild_with_hidden_carriers() -> None:
    rng = Random(2)
    eggs = [g.normal_egg(rng) for _ in range(10000)]
    assert all(g.phenotypes(egg) == ["wild"] for egg in eggs)
    assert 400 < sum("e" in egg["e"] for egg in eggs) < 600
    assert 180 < sum("w" in egg["w"] for egg in eggs) < 320
    assert all(egg["w"] == ["+"] for egg in eggs if egg["sex"] == "m")


def test_mutation_adds_exactly_one_allele_and_never_lethal() -> None:
    egg = g.wild_type("f")
    egg["Cy"] = ["Cy", "+"]
    rng = Random(3)
    loci = set()
    for _ in range(1000):
        child, mutation = g.mutate(rng, egg)
        assert mutation is not None
        loci.add(mutation["locus"])
        assert (
            sum(a != b for locus in g.LOCI for a, b in zip(child[locus], egg[locus], strict=True))
            == 1
        )
        assert not g.lethal(child)
    assert loci == {"w", "y", "e", "vg"}
    assert egg == g.wild_type("f") | {"Cy": ["Cy", "+"]}


def test_combined_phenotypes_and_saturated_mutation() -> None:
    egg = g.wild_type("m")
    for locus in g.LOCI:
        egg[locus] = [locus] * len(egg[locus])
    egg["Cy"] = ["Cy", "+"]
    assert g.phenotypes(egg) == ["white", "yellow", "ebony", "curly", "vestigial"]
    assert g.mutate(Random(1), egg) == (egg, None)


@pytest.mark.parametrize(
    "change",
    [{"sex": "x"}, {"w": ["w"]}, {"e": ["w", "+"]}, {"Cy": ["Cy", "Cy"]}, {"extra": ["+"]}],
)
def test_reject_invalid_or_lethal_parents(change: dict) -> None:
    with pytest.raises(ValueError):
        g.breed(Random(1), g.wild_type("f") | change, g.wild_type("m"))


def test_reject_reversed_sexes() -> None:
    with pytest.raises(ValueError):
        g.breed(Random(1), g.wild_type("m"), g.wild_type("f"))
