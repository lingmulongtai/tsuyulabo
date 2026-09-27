"""Deterministic weekly geometry and path-distance sensory fields; no I/O."""

from __future__ import annotations

import hashlib
import math
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from random import Random
from typing import Any

from .clock import JST

MAX_STEPS = 400
DIRECTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))


def seed_for(week: str, user_id: str = "") -> int:
    return int.from_bytes(hashlib.sha256(f"maze-v1:{week}:{user_id}".encode()).digest()[:8])


def week_at(now: datetime) -> tuple[str, datetime]:
    local = now.astimezone(JST)
    year, week, _ = local.isocalendar()
    monday = (local - timedelta(days=local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return f"{year}-W{week:02d}", monday + timedelta(days=7)


def generate(week: str) -> dict[str, Any]:
    rng = Random(seed_for(week))
    grid = [["#"] * 9 for _ in range(9)]
    grid[1][1] = "."
    stack = [(1, 1)]
    while stack:
        x, y = stack[-1]
        choices = [
            (dx, dy)
            for dx, dy in DIRECTIONS
            if 0 < x + 2 * dx < 8 and 0 < y + 2 * dy < 8 and grid[y + 2 * dy][x + 2 * dx] == "#"
        ]
        if not choices:
            stack.pop()
            continue
        dx, dy = rng.choice(choices)
        grid[y + dy][x + dx] = grid[y + 2 * dy][x + 2 * dx] = "."
        stack.append((x + 2 * dx, y + 2 * dy))
    return {"grid": ["".join(row) for row in grid], "start": [1, 1], "goal": [7, 7]}


def is_open(maze: dict[str, Any], x: int, y: int) -> bool:
    return 0 <= x < 9 and 0 <= y < 9 and maze["grid"][y][x] == "."


def distances(maze: dict[str, Any], origin: tuple[int, int]) -> dict[tuple[int, int], int]:
    result = {origin: 0}
    queue = deque([origin])
    while queue:
        x, y = queue.popleft()
        for dx, dy in DIRECTIONS:
            cell = x + dx, y + dy
            if cell not in result and is_open(maze, *cell):
                result[cell] = result[x, y] + 1
                queue.append(cell)
    return result


def run(
    maze: dict[str, Any],
    placements: list[dict[str, Any]],
    seed: int,
    policy: Callable[[dict[str, Any]], dict[str, float]],
) -> dict[str, Any]:
    goal = tuple(maze["goal"])
    goal_distances = distances(maze, goal)
    fields = [(token["cue"], distances(maze, (token["x"], token["y"]))) for token in placements]

    def sense(cell: tuple[int, int]) -> dict[str, Any]:
        cues = dict.fromkeys((cue for cue, _ in fields), 0.0)
        for cue, field in fields:
            cues[cue] += math.exp(-field[cell] / 3) if cell in field else 0
        return {
            "open": cell in goal_distances,
            "cues": cues,
            "light": (0.3 * math.exp(-goal_distances[cell] / 3) if cell in goal_distances else 0)
            + cues.get("blue_light", 0),
        }

    senses = {cell: sense(cell) for cell in goal_distances}
    rng = Random(seed)
    x, y = maze["start"]
    heading = 1
    frames = [{"x": x, "y": y, "heading": heading}]
    for _ in range(MAX_STEPS):
        observation = {"current": senses[x, y]}
        for action, turn in (("forward", 0), ("left", -1), ("right", 1)):
            dx, dy = DIRECTIONS[(heading + turn) % 4]
            observation[action] = senses.get((x + dx, y + dy)) or sense((x + dx, y + dy))
        probabilities = policy(observation)
        action = rng.choices(list(probabilities), weights=list(probabilities.values()))[0]
        if action == "forward":
            dx, dy = DIRECTIONS[heading]
            if is_open(maze, x + dx, y + dy):
                x, y = x + dx, y + dy
        elif action in {"left", "right"}:
            heading = (heading + (1 if action == "right" else -1)) % 4
        frames.append({"x": x, "y": y, "heading": heading})
        if (x, y) == goal:
            break
    return {
        "reached": (x, y) == goal,
        "steps": len(frames) - 1,
        "distance_left": goal_distances[x, y],
        "frames": frames,
    }
