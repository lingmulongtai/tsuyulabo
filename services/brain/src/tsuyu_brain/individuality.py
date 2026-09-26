"""Seeded individual variation and game-defined trait effects."""

from __future__ import annotations

from collections.abc import Iterable

import torch

from tsuyu_brain.params import BrainParams, default_params

TRAIT_EFFECTS = {
    "right_turner": ("turn_asymmetry", 0.15),
    "left_turner": ("turn_asymmetry", -0.15),
    "light_lover": ("light_gain", 0.30),
    "keen_nose": ("orn_gain", 0.25),
    "brave": ("escape_threshold", 0.20),
    "wanderer": ("walking_gain", 0.30),
    "easygoing": ("walking_gain", -0.30),
    "glutton": ("feeding_gain", 0.25),
}


def generate_individual(traits: Iterable[str], sex: str, seed: int) -> BrainParams:
    traits = tuple(traits)
    if sex not in {"m", "f"}:
        raise ValueError("sex must be m or f")
    if len(set(traits)) != len(traits) or set(traits) - TRAIT_EFFECTS.keys():
        raise ValueError("duplicate or unknown trait")
    for pair in ({"right_turner", "left_turner"}, {"wanderer", "easygoing"}):
        if pair <= set(traits):
            raise ValueError("mutually exclusive traits")
    values = default_params().to_dict()
    generator = torch.Generator().manual_seed(seed)
    noise = torch.randn(len(values), generator=generator).tolist()
    for (name, value), deviation in zip(values.items(), noise, strict=True):
        values[name] = (
            value * max(0.5, 1 + 0.025 * deviation)
            if name != "turn_asymmetry"
            else 0.015 * deviation
        )
    for trait in traits:
        name, effect = TRAIT_EFFECTS[trait]
        if name == "turn_asymmetry":
            values[name] += effect
        else:
            values[name] *= 1 + effect
    # Sex is validated, but the spec defines no sex-dependent physiology.
    return BrainParams(**values)
