from __future__ import annotations

from random import Random

from .. import constants as c
from .common import JsonObject, VerifyResult, integer, times_reason


def _neighbors(cell: int, n: int) -> list[int]:
    r, col = divmod(cell, n)
    return [
        row * n + column
        for row, column in ((r - 1, col), (r + 1, col), (r, col - 1), (r, col + 1))
        if 0 <= row < n and 0 <= column < n
    ]


def hamiltonian_path(rng: Random, n: int) -> list[int]:
    """Warnsdorff's minimum onward degree, random ties, restart on dead ends."""
    if n not in c.CHECKPOINT_COUNTS:
        raise ValueError("unsupported training size")
    neighbors = [_neighbors(cell, n) for cell in range(n * n)]
    while True:
        path = [rng.randrange(n * n)]
        visited = set(path)
        while len(path) < n * n:
            candidates = [cell for cell in neighbors[path[-1]] if cell not in visited]
            if not candidates:
                break
            rng.shuffle(candidates)
            cell = min(candidates, key=lambda cell: sum(x not in visited for x in neighbors[cell]))
            visited.add(cell)
            path.append(cell)
        if len(path) == n * n:
            return path


def generate(rng: Random, context: JsonObject) -> tuple[JsonObject, JsonObject]:
    day = context.get("research_day", 2)
    cue, valence = context.get("cue", "banana"), context.get("valence", "reward")
    if day not in c.TRAINING_SIZES or cue not in c.CUES or valence not in c.VALENCES:
        raise ValueError("invalid training context")
    n = c.TRAINING_SIZES[day]
    path = hamiltonian_path(rng, n)
    count = c.CHECKPOINT_COUNTS[n]
    indices = (
        [0]
        + [
            round(k * (len(path) - 1) / (count - 1)) + rng.randint(-1, 1)
            for k in range(1, count - 1)
        ]
        + [len(path) - 1]
    )
    checkpoints = [{"cell": path[index], "k": k} for k, index in enumerate(indices, 1)]
    return {"n": n, "checkpoints": checkpoints, "cue": cue, "valence": valence}, {"path": path}


def verify(params: JsonObject, submission: JsonObject) -> VerifyResult:
    n, path = params["n"], submission.get("path")
    if not isinstance(path, list) or len(path) != n * n:
        return VerifyResult(False, "wrong_length")
    if any(not integer(cell) or not 0 <= cell < n * n for cell in path):
        return VerifyResult(False, "out_of_bounds")
    if len(set(path)) != len(path):
        return VerifyResult(False, "revisit")
    if any(b not in _neighbors(a, n) for a, b in zip(path, path[1:], strict=False)):
        return VerifyResult(False, "not_adjacent")
    checkpoints = sorted(params["checkpoints"], key=lambda checkpoint: checkpoint["k"])
    if path[0] != checkpoints[0]["cell"]:
        return VerifyResult(False, "bad_start")
    if path[-1] != checkpoints[-1]["cell"]:
        return VerifyResult(False, "bad_end")
    positions = [path.index(checkpoint["cell"]) for checkpoint in checkpoints]
    if positions != sorted(positions):
        return VerifyResult(False, "checkpoint_order")
    elapsed = submission.get("elapsed_ms")
    reason = times_reason([], elapsed)
    if reason:
        return VerifyResult(False, reason)
    scale = n * n / c.TRAINING_SCALE_CELLS
    stars = (
        3
        if elapsed < c.TRAINING_THREE_STAR_MS * scale
        else (2 if elapsed < c.TRAINING_TWO_STAR_MS * scale else 1)
    )
    return VerifyResult(True, stars=stars)


def roll(rng: Random, stars: int) -> JsonObject:
    if stars not in (1, 2, 3):
        raise ValueError("stars must be 1, 2 or 3")
    hirameki = rng.random() < (c.HIRAMEKI_THREE_STAR_CHANCE if stars == 3 else c.HIRAMEKI_CHANCE)
    strength = stars * c.LEARNING_PER_STAR * (c.HIRAMEKI_MULTIPLIER if hirameki else 1)
    return {"hirameki": hirameki, "learning_strength": strength}


def skill_unlocked(cue: str, value: float) -> str | None:
    """Call with the association value returned by the brain, not puzzle strength."""
    if cue not in c.CUES or not -1 <= value <= 1:
        raise ValueError("invalid association")
    if abs(value) <= c.SKILL_THRESHOLD:
        return None
    return c.SKILL_UNLOCKS[cue]["reward" if value > 0 else "punish"][0]
