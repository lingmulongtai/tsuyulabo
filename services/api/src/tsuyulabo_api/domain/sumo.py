"""Pure, seeded one-dimensional projection of a circular pushing mat."""

from __future__ import annotations

import random
from collections.abc import Callable

Action = str
Policy = Callable[[dict[str, float]], dict[Action, float]]


def _choose(rng: random.Random, weights: dict[str, float]) -> str:
    roll = rng.random()
    for action, weight in weights.items():
        roll -= weight
        if roll <= 0:
            return action
    return next(reversed(weights))


def run(left: Policy, right: Policy, seed: int, levels: tuple[int, int]) -> dict:
    """Return a replay; both policies see the same pre-tick geometry."""
    rng = random.Random(seed)
    positions = [-2.0, 2.0]
    retreats = [0, 0]
    stamina = [1 + min(max(level - 1, 0), 10) * 0.01 for level in levels]
    flourish = [False, False]
    frames: list[dict] = []
    winner: int | None = None
    reason = "position"
    for tick in range(1, 31):
        distance = positions[1] - positions[0]
        actions = [
            _choose(
                rng,
                policy(
                    {
                        "distance": distance,
                        "food_distance": abs(positions[index]),
                        "threat": 0.8 if flourish[1 - index] else (0.4 if distance < 1.6 else 0.1),
                        "stamina": stamina[index],
                    }
                ),
            )
            for index, policy in enumerate((left, right))
        ]
        push = [0.0, 0.0]
        for index, action in enumerate(actions):
            direction = 1 if index == 0 else -1
            if action == "approach":
                positions[index] += direction * 0.38
            elif action == "retreat":
                positions[index] -= direction * 0.38
                retreats[index] += 1
            elif action == "lunge" and distance < 1.8 and stamina[index] >= 0.2:
                push[index] = 0.55 + (0.3 if flourish[index] else 0)
                stamina[index] = max(0, stamina[index] - 0.12)
            else:
                stamina[index] = min(1.1, stamina[index] + 0.04)
        positions[0] -= push[1]
        positions[1] += push[0]
        flourish = [action == "wing_threat" for action in actions]
        frames.append(
            {
                "tick": tick,
                "positions": positions.copy(),
                "actions": actions,
                "push": push.copy(),
                "retreats": retreats.copy(),
            }
        )
        lost = [abs(positions[index]) > 4 or retreats[index] >= 3 for index in (0, 1)]
        if any(lost):
            reason = "ring" if any(abs(position) > 4 for position in positions) else "retreats"
            winner = (1 if lost[0] else 0) if lost[0] != lost[1] else rng.randrange(2)
            break
    if winner is None:
        margin = abs(positions[0]) - abs(positions[1])
        winner = (0 if margin < 0 else 1) if margin != 0 else rng.randrange(2)
    return {"winner": winner, "reason": reason, "frames": frames}
