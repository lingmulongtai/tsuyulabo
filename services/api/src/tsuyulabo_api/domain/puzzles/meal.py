from __future__ import annotations

from math import floor
from random import Random

from .. import constants as c
from .common import JsonObject, VerifyResult, integer, times_reason


def generate(rng: Random, context: JsonObject) -> tuple[JsonObject, JsonObject]:
    theme = context.get("theme")
    if theme is None:
        theme = rng.choice(c.MATERIALS)
    if theme not in c.MATERIALS:
        raise ValueError("unknown theme")
    pieces = [
        {
            "shape": rng.choices(tuple(c.SHAPES), weights=tuple(c.SHAPE_WEIGHTS.values()))[0],
            "ingredient": rng.choices(
                c.MATERIALS,
                weights=[
                    c.THEME_WEIGHT if ingredient == theme else c.OTHER_INGREDIENT_WEIGHT
                    for ingredient in c.MATERIALS
                ],
            )[0],
        }
        for _ in range(c.MEAL_PIECE_COUNT)
    ]
    return {
        "rows": c.MEAL_ROWS,
        "cols": c.MEAL_COLS,
        "time_limit_ms": c.MEAL_TIME_LIMIT_MS,
        "hand_size": c.MEAL_HAND_SIZE,
        "theme": theme,
        "pieces": pieces,
    }, {}


def verify(params: JsonObject, submission: JsonObject) -> VerifyResult:
    moves = submission.get("moves")
    if (
        not isinstance(moves, list)
        or len(moves) > len(params["pieces"])
        or any(not isinstance(m, dict) for m in moves)
    ):
        return VerifyResult(False, "wrong_length")
    reason = times_reason(
        [m.get("t") for m in moves],
        submission.get("elapsed_ms"),
        limit=params["time_limit_ms"] + c.MEAL_TIME_GRACE_MS,
    )
    if reason:
        return VerifyResult(False, reason)
    rows, cols, pieces, hand_size = (
        params["rows"],
        params["cols"],
        params["pieces"],
        params["hand_size"],
    )
    board: dict[tuple[int, int], str] = {}
    placed: set[int] = set()
    score = lines = max_combo = theme_cells = combo = 0
    for move in moves:
        p, r, col = move.get("p"), move.get("r"), move.get("c")
        if not integer(p):
            return VerifyResult(False, "not_in_hand")
        if p in placed:
            return VerifyResult(False, "already_placed")
        hand = len(placed) // hand_size
        if p < hand * hand_size or p >= min((hand + 1) * hand_size, len(pieces)):
            return VerifyResult(False, "not_in_hand")
        if not integer(r) or not integer(col):
            return VerifyResult(False, "out_of_bounds")
        cells = [(r + dr, col + dc) for dr, dc in c.SHAPES[pieces[p]["shape"]]]
        if any(not (0 <= row < rows and 0 <= column < cols) for row, column in cells):
            return VerifyResult(False, "out_of_bounds")
        if any(cell in board for cell in cells):
            return VerifyResult(False, "cell_occupied")
        board.update(dict.fromkeys(cells, pieces[p]["ingredient"]))
        placed.add(p)
        full_rows = [
            row for row in range(rows) if all((row, column) in board for column in range(cols))
        ]
        full_cols = [
            column for column in range(cols) if all((row, column) in board for row in range(rows))
        ]
        cleared = {cell for cell in board if cell[0] in full_rows or cell[1] in full_cols}
        count = len(full_rows) + len(full_cols)
        combo = combo + 1 if count else 0
        themed = sum(board[cell] == params["theme"] for cell in cleared)
        line_score = c.LINE_SCORE * count * (count + 1) // 2
        multiplier = 1 + c.COMBO_STEP * (combo - 1) if combo else 0
        score += len(cells) + floor(line_score * multiplier) + themed * c.THEME_CELL_SCORE
        lines += count
        max_combo = max(max_combo, combo)
        theme_cells += themed
        for cell in cleared:
            del board[cell]
    return VerifyResult(
        True, score=score, lines=lines, max_combo=max_combo, theme_cells=theme_cells
    )


def great_success_probability(score: int, research_day: int, team_great_bonus: float = 0) -> float:
    if score < 0 or team_great_bonus < 0:
        raise ValueError("negative score or bonus")
    probability = min(c.GREAT_BASE_CAP, c.GREAT_BASE_CHANCE + score / c.GREAT_SCORE_DIVISOR)
    probability += min(c.TEAM_GREAT_BONUS_CAP, team_great_bonus)
    if research_day == c.ECLOSION_DAY:
        probability *= c.FINAL_DAY_MULTIPLIER
    return min(c.GREAT_FINAL_CAP, probability)


def roll(rng: Random, score: int, research_day: int, team_great_bonus: float = 0) -> JsonObject:
    great = rng.random() < great_success_probability(score, research_day, team_great_bonus)
    growth = score / c.GROWTH_SCORE_DIVISOR
    if research_day == c.LARVA3_DAY:
        growth *= c.LARVA3_GROWTH_MULTIPLIER
    if great:
        growth *= c.GREAT_GROWTH_MULTIPLIER
    return {
        "great_success": great,
        "effects": {"growth": growth, "hunger": c.GREAT_MEAL_HUNGER if great else c.MEAL_HUNGER},
    }
