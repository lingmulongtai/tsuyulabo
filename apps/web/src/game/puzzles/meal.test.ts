import { describe, expect, it } from "vitest";
import {
  SHAPES, canPlace, createMealGame, currentHand, hasAnyMove, isOver, place, verifyMeal,
} from "./meal";
import type { MealParams, MealPiece, MealSubmission, Shape } from "./types";

function params(pieces: readonly MealPiece[], rows = 8, cols = 8): MealParams {
  return { rows, cols, time_limit_ms: 30000, hand_size: 3, theme: "banana", pieces };
}
const single: MealPiece = { shape: "m1", ingredient: "banana" };
const defaults = params(Array.from({ length: 9 }, () => single));

describe("meal", () => {
  it("creates independent empty rows, no score and the first hand", () => {
    const state = createMealGame(defaults);
    expect(state.board).toEqual(Array.from({ length: 8 }, () => Array(8).fill(null)));
    expect(state.board[0]).not.toBe(state.board[1]);
    expect(state.score).toBe(0);
    expect(currentHand(state)).toEqual([0, 1, 2]);
    expect(hasAnyMove(state)).toBe(true);
    expect(isOver(state, 29999)).toBe(false);
    expect(isOver(state, 30000)).toBe(true);
  });

  it.each(Object.keys(SHAPES) as Shape[])("places %s with the specified offsets", (shape) => {
    const state = createMealGame(params([{ shape, ingredient: "apple" }]));
    const result = place(state, 0, 1, 2, 0);
    expect(result.placedCells).toEqual(SHAPES[shape].map(([dr, dc]) => ({
      r: dr + 1, c: dc + 2, ingredient: "apple",
    })));
    expect(result.moveScore).toBe(SHAPES[shape].length);
    expect(result.state.moves).toEqual([{ p: 0, r: 1, c: 2, t: 0 }]);
    expect(state.board.flat().every((cell) => cell === null)).toBe(true);
    expect(state.moves).toEqual([]);
  });

  it("preserves the asymmetric offsets and nine-cell square", () => {
    expect(SHAPES.l3d).toEqual([[0, 1], [1, 0], [1, 1]]);
    expect(SHAPES.s4).toEqual([[0, 1], [0, 2], [1, 0], [1, 1]]);
    expect(SHAPES.o9).toHaveLength(9);
    expect(new Set(SHAPES.o9.map(([r, c]) => r * 3 + c)).size).toBe(9);
  });

  it("deals in groups of three, in any placement order, including a partial final hand", () => {
    let state = createMealGame(params([single, single, single, single]));
    state = place(state, 2, 0, 0, 0).state;
    expect(currentHand(state)).toEqual([0, 1]);
    expect(canPlace(state, 3, 0, 1)).toBe(false);
    state = place(state, 0, 0, 1, 0).state;
    state = place(state, 1, 0, 2, 0).state;
    expect(currentHand(state)).toEqual([3]);
    state = place(state, 3, 0, 3, 0).state;
    expect(currentHand(state)).toEqual([]);
    expect(hasAnyMove(state)).toBe(false);
    expect(isOver(state, 0)).toBe(true);
  });

  it("counts a row/column intersection once and keeps the cleared ingredients", () => {
    const config = params([single, { ...single, ingredient: "apple" }, single], 2, 2);
    let state = createMealGame(config);
    state = place(state, 0, 0, 1, 10).state;
    state = place(state, 1, 1, 0, 20).state;
    const result = place(state, 2, 0, 0, 30);
    expect(result.clearedRows).toEqual([0]);
    expect(result.clearedCols).toEqual([0]);
    expect(result.clearedCells).toEqual([
      { r: 0, c: 0, ingredient: "banana" },
      { r: 0, c: 1, ingredient: "banana" },
      { r: 1, c: 0, ingredient: "apple" },
    ]);
    expect(result.moveScore).toBe(331);
    expect(result.state.board).toEqual([[null, null], [null, null]]);
    expect(verifyMeal(config, { moves: result.state.moves, elapsed_ms: 30 })).toEqual({
      valid: true, score: 333, lines: 2, max_combo: 1, theme_cells: 2,
    });
  });

  it("chains multipliers, resets on no clear, and keeps max combo", () => {
    const row: MealPiece = { shape: "d2h", ingredient: "apple" };
    let state = createMealGame(params([row, row, row, single, row], 3, 2));
    for (const [p, score] of [102, 152, 202].entries()) {
      const result = place(state, p, 0, 0, p);
      expect(result.moveScore).toBe(score);
      expect(result.combo).toBe(p + 1);
      state = result.state;
    }
    state = place(state, 3, 1, 0, 4).state;
    expect(state.combo).toBe(0);
    const result = place(state, 4, 0, 0, 5);
    expect(result.moveScore).toBe(102);
    expect(result.combo).toBe(1);
    expect(result.state.max_combo).toBe(3);
  });

  it("reports no move when every remaining piece is blocked", () => {
    const state = createMealGame(params([{ shape: "o9", ingredient: "agar" }], 2, 2));
    expect(hasAnyMove(state)).toBe(false);
    expect(isOver(state, 0)).toBe(true);
  });

  const move = { p: 0, r: 0, c: 0, t: 10 };
  it.each([
    ["not_in_hand", [{ ...move, p: 3 }]],
    ["not_in_hand", [{ ...move, p: -1 }]],
    ["already_placed", [move, { ...move, c: 1 }]],
    ["out_of_bounds", [{ ...move, r: -1 }]],
    ["out_of_bounds", [{ ...move, c: 8 }]],
    ["out_of_bounds", [{ ...move, c: 0.5 }]],
    ["cell_occupied", [move, { ...move, p: 1 }]],
    ["time_exceeded", [{ ...move, t: 31501 }]],
    ["non_monotonic_time", [move, { ...move, p: 1, c: 1, t: 9 }]],
    ["non_monotonic_time", [{ ...move, t: -1 }]],
    ["non_monotonic_time", [{ ...move, t: NaN }]],
  ] as const)("rejects %s", (reason, moves) => {
    expect(verifyMeal(defaults, { moves, elapsed_ms: 40000 })).toEqual({ valid: false, reason });
  });

  it("checks elapsed time and accepts the inclusive 1500 ms grace", () => {
    expect(verifyMeal(defaults, { moves: [{ ...move, t: 31500 }], elapsed_ms: 31500 }).valid)
      .toBe(true);
    for (const elapsed_ms of [9, -1, NaN, Infinity]) {
      expect(verifyMeal(defaults, { moves: [move], elapsed_ms })).toEqual({
        valid: false, reason: "non_monotonic_time",
      });
    }
    const empty: MealSubmission = { moves: [], elapsed_ms: 30000 };
    expect(verifyMeal(defaults, empty)).toEqual({
      valid: true, score: 0, lines: 0, max_combo: 0, theme_cells: 0,
    });
  });

  it("rejects illegal placements without changing state", () => {
    const state = createMealGame(defaults);
    expect(canPlace(state, 0, 8, 0)).toBe(false);
    expect(() => place(state, 0, 8, 0, 0)).toThrow("out_of_bounds");
    expect(state.moves).toHaveLength(0);
  });
});
