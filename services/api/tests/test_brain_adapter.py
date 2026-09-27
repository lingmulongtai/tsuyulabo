from __future__ import annotations

from .game_support import FakeBrain


def test_snapshot_reconstructs_learning_and_individuality() -> None:
    brain = FakeBrain()
    initial = brain.new()
    learned, value = brain.train(initial, "banana", "reward", 0.72, 1)
    assert value == 0.72 and initial["training"] == []
    adult, params = brain.eclose(learned, ["brave", "glutton"], "f", 42)
    assert params["traits"] == ["brave", "glutton"]
    assert brain.preferences(adult)["banana"] == 0.72
    assert brain.experiment(adult, "banana", 100, 0) == {"toward": 86, "away": 14}
    assert brain.preferences(adult)["banana"] == 0.72
