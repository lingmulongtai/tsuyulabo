from __future__ import annotations

import hashlib
from datetime import date
from random import Random

from .common import JsonObject
from .training import generate_board


def generate(day: date) -> tuple[JsonObject, JsonObject]:
    seed = int.from_bytes(hashlib.sha256(f"daily-circuit:{day.isoformat()}".encode()).digest())
    params, secret = generate_board(Random(seed), 7, 9)
    return params | {"cue": "banana", "valence": "reward"}, secret


def shizuku_for(elapsed_ms: int) -> int:
    if elapsed_ms < 0:
        raise ValueError("elapsed time must be nonnegative")
    return 60 if elapsed_ms < 20_000 else 40 if elapsed_ms < 40_000 else 20
