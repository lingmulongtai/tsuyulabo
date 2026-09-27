from __future__ import annotations

from typing import Any

from tsuyulabo_api.db.models import Puzzle
from tsuyulabo_api.domain.constants import SHAPES
from tsuyulabo_api.domain.puzzles.temperature import temperature_at

from .game_support import GameClient


def solve_meal(params: dict[str, Any]) -> dict[str, Any]:
    occupied: set[tuple[int, int]] = set()
    moves = []
    pieces = params["pieces"]
    for start in range(0, len(pieces), 3):
        hand = list(range(start, min(start + 3, len(pieces))))
        while hand:
            best = None
            for p in hand:
                for row in range(8):
                    for col in range(8):
                        cells = {(row + r, col + c) for r, c in SHAPES[pieces[p]["shape"]]}
                        if any(r >= 8 or c >= 8 for r, c in cells) or occupied & cells:
                            continue
                        board = occupied | cells
                        rows = {r for r in range(8) if all((r, c) in board for c in range(8))}
                        cols = {c for c in range(8) if all((r, c) in board for r in range(8))}
                        priority = (len(rows) + len(cols)) * 100 + sum(
                            (r + dr, c + dc) in board
                            for r, c in cells
                            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                        )
                        if best is None or priority > best[0]:
                            best = (priority, p, row, col, board, rows, cols)
            if best is None:
                return {"moves": moves, "elapsed_ms": 30000}
            _, p, row, col, board, rows, cols = best
            moves.append({"p": p, "r": row, "c": col, "t": (len(moves) + 1) * 300})
            occupied = {(r, c) for r, c in board if r not in rows and c not in cols}
            hand.remove(p)
    return {"moves": moves, "elapsed_ms": 30000}


def solve(kind: str, params: dict, secret: dict) -> dict:
    if kind == "meal":
        return solve_meal(params)
    if kind == "training":
        return {"path": secret["path"], "elapsed_ms": 5000}
    if kind == "pupation_site":
        return {"choice": secret["winning_id"]}
    if kind == "temperature":
        stop = min(range(params["period_ms"]), key=lambda t: abs(temperature_at(params, t) - 25))
        return {"stop_ms": stop, "elapsed_ms": stop}
    period, phase = params["period_ms"], params["phase"]
    first = ((0.25 - phase) % 0.5) * period
    taps = [round(first + k * period / 2) for k in range(3)]
    return {"taps": taps, "elapsed_ms": taps[-1]}


async def play(game: GameClient, sessions: Any, kind: str) -> dict:
    request = {"kind": kind}
    if kind == "training":
        request |= {"cue": "banana", "valence": "reward"}
    response = await game.post("/v1/puzzles", request)
    assert response.status_code == 201, response.text
    issued = response.json()
    async with sessions() as session:
        puzzle = await session.get(Puzzle, issued["puzzle_id"])
        submission = solve(kind, puzzle.params, puzzle.secret)
    game.clock.advance(submission.get("elapsed_ms", 0) / 1000)
    response = await game.post(f"/v1/puzzles/{puzzle.id}/submit", submission)
    assert response.status_code == 200, response.text
    return response.json()
