from __future__ import annotations

from datetime import date, timedelta

import pytest
from tsuyulabo_api.domain.puzzles import daily_circuit, training


def test_daily_boards_are_deterministic_solvable_and_vary() -> None:
    boards = []
    for offset in range(60):
        day = date(2026, 1, 1) + timedelta(days=offset)
        params, secret = daily_circuit.generate(day)
        assert (params, secret) == daily_circuit.generate(day)
        assert params["n"] == 7
        assert len(params["checkpoints"]) == 9
        assert training.verify(params, secret | {"elapsed_ms": 20_000}).valid
        boards.append(params)
    assert all(a != b for a, b in zip(boards, boards[1:], strict=False))


@pytest.mark.parametrize(
    "elapsed,reward", [(0, 60), (19999, 60), (20000, 40), (39999, 40), (40000, 20), (599999, 20)]
)
def test_reward_boundaries(elapsed: int, reward: int) -> None:
    assert daily_circuit.shizuku_for(elapsed) == reward
