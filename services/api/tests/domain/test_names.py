from __future__ import annotations

from random import Random

from tsuyulabo_api.domain.names import NAME_POOL, THEMED_NAMES, pick_name


def test_pool_and_seeded_selection() -> None:
    assert len(NAME_POOL) == len(set(NAME_POOL)) == 60
    assert all(1 <= len(name) <= 12 for name in NAME_POOL)
    assert pick_name(Random(42), set()) == pick_name(Random(42), set())


def test_exhaust_pool_without_duplicates_or_mutating_taken() -> None:
    taken: set[str] = set()
    rng = Random(12)
    for _ in NAME_POOL:
        before = taken.copy()
        name = pick_name(rng, taken)
        assert taken == before
        assert name in NAME_POOL and name not in taken
        taken.add(name)
    base = Random(42).choice(NAME_POOL)
    taken.add(f"{base}2")
    assert pick_name(Random(42), taken) == f"{base}3"


def test_themes_fall_back_to_unused_pool() -> None:
    for strain, names in THEMED_NAMES.items():
        assert pick_name(Random(1), set(), strain=strain) in names
        assert pick_name(Random(1), set(names), strain=strain) not in names
    assert pick_name(Random(1), set(), strain="wild") in NAME_POOL
