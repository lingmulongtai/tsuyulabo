from __future__ import annotations

from tsuyu_brain.api import generate_individual, new_fly_state, sumo_policy


def test_brave_retreats_less_and_wanderer_approaches_more() -> None:
    observation = {"distance": 2.0, "food_distance": 2.0, "threat": 0.8, "stamina": 1.0}
    ordinary = new_fly_state(generate_individual([], "m", 12))
    brave = new_fly_state(generate_individual(["brave"], "m", 12))
    wanderer = new_fly_state(generate_individual(["wanderer"], "m", 12))
    base = sumo_policy(ordinary, observation)
    assert sumo_policy(brave, observation)["retreat"] < base["retreat"]
    assert sumo_policy(wanderer, observation)["approach"] > base["approach"]
    assert abs(sum(base.values()) - 1) < 1e-9
