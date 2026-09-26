"""Compact, immutable individual parameters; all times are milliseconds."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BrainParams:
    orn_gain: float = 1.0
    pn_gain: float = 1.0
    kc_gain: float = 1.0
    visual_gain: float = 1.0
    sugar_gain: float = 1.0
    bitter_gain: float = 1.0
    feeding_gain: float = 1.0
    escape_gain: float = 1.0
    light_gain: float = 1.0
    walking_gain: float = 1.0
    grooming_gain: float = 1.0
    mbon_gain: float = 1.0
    threshold: float = 1.0
    kc_threshold: float = 1.0
    feeding_threshold: float = 1.0
    escape_threshold: float = 1.0
    steering_threshold: float = 1.0
    grooming_threshold: float = 1.0
    mbon_threshold: float = 1.0
    turn_asymmetry: float = 0.0
    walking_current: float = 1.15
    input_rate_hz: float = 180.0
    input_current: float = 6.0
    learning_rate: float = 0.65

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            if name != "turn_asymmetry" and value <= 0:
                raise ValueError(f"{name} must be positive")
        if abs(self.turn_asymmetry) >= 1:
            raise ValueError("turn_asymmetry must be between -1 and 1")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> BrainParams:
        return cls(**json.loads(payload))


def default_params() -> BrainParams:
    return BrainParams()
