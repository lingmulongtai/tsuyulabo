from __future__ import annotations

import pytest
from tsuyu_brain.individuality import TRAIT_EFFECTS, generate_individual


@pytest.mark.parametrize("trait", TRAIT_EFFECTS)
def test_trait_effects_and_determinism(trait: str) -> None:
    baseline = generate_individual([], "m", 19)
    individual = generate_individual([trait], "m", 19)
    assert individual == generate_individual([trait], "m", 19)
    name, effect = TRAIT_EFFECTS[trait]
    expected = (
        getattr(baseline, name) + effect
        if name == "turn_asymmetry"
        else getattr(baseline, name) * (1 + effect)
    )
    assert getattr(individual, name) == pytest.approx(expected)
    assert baseline != generate_individual([], "m", 20)


@pytest.mark.parametrize(
    "traits",
    [["right_turner", "left_turner"], ["wanderer", "easygoing"], ["unknown"], ["brave", "brave"]],
)
def test_invalid_traits(traits: list[str]) -> None:
    with pytest.raises(ValueError):
        generate_individual(traits, "f", 0)
