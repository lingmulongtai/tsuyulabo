from __future__ import annotations

from random import Random

from tsuyulabo_api.db.models import Adult
from tsuyulabo_api.domain.adults import add_exp
from tsuyulabo_api.services.adults import apply_progress, payload, progress

from .game_support import FakeBrain


def test_progress_and_cached_preferences() -> None:
    adult = Adult(
        stars=5,
        level=9,
        exp=89,
        subskills=[],
        energy=100,
        preferences={"banana": 0},
        brain_snapshot=FakeBrain().new(),
    )
    apply_progress(adult, add_exp(progress(adult), 1, Random(42)))
    assert adult.level == 10 and len(adult.subskills) == 1
    assert payload(adult, FakeBrain())["preferences"]["banana"] == 0
    adult.brain_snapshot = {}  # Cached reads do not ask the engine again.
    assert payload(adult, FakeBrain())["preferences"]["banana"] == 0
