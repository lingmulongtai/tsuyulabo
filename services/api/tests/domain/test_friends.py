from __future__ import annotations

from random import Random

import pytest
from tsuyulabo_api.domain.friends import generate_code, validate_code


def test_generation() -> None:
    rng = Random(1)
    codes = {generate_code(rng) for _ in range(1000)}
    assert len(codes) == 1000 and all(validate_code(code) for code in codes)
    assert generate_code(Random(123)) == generate_code(Random(123))


@pytest.mark.parametrize(
    "code",
    [
        None,
        "",
        "ABCDEFG",
        "ABCDEFGHJ",
        "abcdefg2",
        "ABCDEFG0",
        "ABCDEFG1",
        "ABCDEFGO",
        "ABCDEFGI",
        "ABCDEFG ",
        "ＡBCDEFGH",
    ],
)
def test_invalid(code: object) -> None:
    assert not validate_code(code)
