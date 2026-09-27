from __future__ import annotations

from tsuyulabo_api.domain.sumo import run


def test_replay_is_seeded_and_caps_level_bonus() -> None:
    def policy(_: dict[str, float]) -> dict[str, float]:
        return {"approach": 0.5, "lunge": 0.3, "wing_threat": 0.1, "retreat": 0.1}

    result = run(policy, policy, 53, (1, 50))
    assert result == run(policy, policy, 53, (1, 11))
    assert result["winner"] in (0, 1)
    assert len(result["frames"]) <= 30
