"""Independent-locus Mendelian model; see docs/specs/genetics.md for limits."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import TypedDict

from .constants import HIDDEN_CARRIER_CHANCE

LOCI = ("w", "y", "e", "Cy", "vg")
X_LINKED = ("w", "y")
TRAITS = {"w": "white", "y": "yellow", "e": "ebony", "Cy": "curly", "vg": "vestigial"}


class Genotype(TypedDict):
    sex: str
    w: list[str]
    y: list[str]
    e: list[str]
    Cy: list[str]
    vg: list[str]


class Mutation(TypedDict):
    locus: str
    copy: int


def wild_type(sex: str) -> Genotype:
    if sex not in ("f", "m"):
        raise ValueError("sex must be f or m")
    return Genotype(
        sex=sex,
        w=["+"] * (2 if sex == "f" else 1),
        y=["+"] * (2 if sex == "f" else 1),
        e=["+", "+"],
        Cy=["+", "+"],
        vg=["+", "+"],
    )


def validate(genotype: Genotype) -> None:
    expected = wild_type(genotype["sex"])
    if set(genotype) != set(expected):
        raise ValueError("unknown or missing locus")
    for locus in LOCI:
        alleles = genotype[locus]
        if len(alleles) != len(expected[locus]) or any(a not in ("+", locus) for a in alleles):
            raise ValueError(f"invalid alleles at {locus}")


def lethal(genotype: Genotype) -> bool:
    return genotype["Cy"] == ["Cy", "Cy"]


def phenotypes(genotype: Genotype) -> list[str]:
    validate(genotype)
    if lethal(genotype):
        raise ValueError("Cy/Cy has no viable adult phenotype")
    return [
        TRAITS[locus]
        for locus in LOCI
        if ("Cy" in genotype[locus] if locus == "Cy" else all(a == locus for a in genotype[locus]))
    ] or ["wild"]


def normal_egg(rng: Random) -> Genotype:
    genotype = wild_type(rng.choice(("f", "m")))
    for locus in ("w", "y", "e", "vg"):
        if len(genotype[locus]) == 2 and rng.random() < HIDDEN_CARRIER_CHANCE:
            genotype[locus][rng.randrange(2)] = locus
    return genotype


@dataclass(frozen=True)
class Offspring:
    genotype: Genotype
    lethal_redraws: int


def breed(rng: Random, mother: Genotype, father: Genotype) -> Offspring:
    for parent, sex in ((mother, "f"), (father, "m")):
        validate(parent)
        if parent["sex"] != sex or lethal(parent):
            raise ValueError("parents must be a viable female and male")
    rejected = 0
    while True:
        child = wild_type(rng.choice(("f", "m")))
        for locus in LOCI:
            child[locus] = [rng.choice(mother[locus])]
            if locus not in X_LINKED or child["sex"] == "f":
                child[locus].append(rng.choice(father[locus]))
        if not lethal(child):
            return Offspring(child, rejected)
        rejected += 1


def mutate(rng: Random, genotype: Genotype) -> tuple[Genotype, Mutation | None]:
    """Add one mutant allele without mutating the supplied egg or making Cy/Cy."""
    phenotypes(genotype)  # Validate viability before choosing a mutation.
    result = Genotype(**{key: value[:] for key, value in genotype.items()})
    eligible = [
        locus
        for locus in LOCI
        if "+" in genotype[locus] and not (locus == "Cy" and "Cy" in genotype[locus])
    ]
    if not eligible:
        return result, None
    locus = rng.choice(eligible)
    copy = rng.choice([i for i, allele in enumerate(genotype[locus]) if allele == "+"])
    result[locus][copy] = locus
    return result, Mutation(locus=locus, copy=copy)
