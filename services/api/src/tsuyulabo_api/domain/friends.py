from __future__ import annotations

from random import Random

from .constants import FRIEND_CODE_ALPHABET, FRIEND_CODE_LENGTH


def generate_code(rng: Random) -> str:
    """The storage layer must retry collisions against its unique index."""
    return "".join(rng.choice(FRIEND_CODE_ALPHABET) for _ in range(FRIEND_CODE_LENGTH))


def validate_code(code: object) -> bool:
    return (
        isinstance(code, str)
        and len(code) == FRIEND_CODE_LENGTH
        and all(char in FRIEND_CODE_ALPHABET for char in code)
    )
