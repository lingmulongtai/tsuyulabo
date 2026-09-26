import { describe, expect, it } from "vitest";
import {
  cellToRC, createTrainingGame, isSolved, neighbors, rcToCell,
  starsFor, truncateTo, tryStep, verifyTraining,
} from "./training";
import type { TrainingParams } from "./types";

const params: TrainingParams = {
  n: 3, cue: "banana", valence: "reward",
  checkpoints: [{ cell: 0, k: 1 }, { cell: 5, k: 2 }, { cell: 8, k: 3 }],
};
const solution = [0, 1, 2, 5, 4, 3, 6, 7, 8];

describe("training", () => {
  it("converts cells and enumerates neighbors without wrapping", () => {
    for (let cell = 0; cell < 9; cell++) {
      const { r, c } = cellToRC(3, cell);
      expect(rcToCell(3, r, c)).toBe(cell);
    }
    expect(cellToRC(5, 8)).toEqual({ r: 1, c: 3 });
    expect(neighbors(3, 0)).toEqual([1, 3]);
    expect(neighbors(3, 2)).toEqual([5, 1]);
    expect(neighbors(3, 4)).toEqual([1, 5, 7, 3]);
    expect(neighbors(3, 8)).toEqual([5, 7]);
    expect(neighbors(1, 0)).toEqual([]);
    for (const cell of [-1, 9, NaN, 0.5]) expect(neighbors(3, cell)).toEqual([]);
  });

  it("only starts at checkpoint one and solves without mutating earlier states", () => {
    const initial = createTrainingGame(params);
    expect(initial.path).toEqual([]);
    expect(isSolved(initial)).toBe(false);
    for (const cell of [1, 5, -1, 9, NaN]) expect(tryStep(initial, cell)).toBe(initial);
    const solved = solution.reduce(tryStep, initial);
    expect(solved.path).toEqual(solution);
    expect(isSolved(solved)).toBe(true);
    expect(initial.path).toEqual([]);
    expect(verifyTraining(params, { path: solution, elapsed_ms: 3000 })).toEqual({
      valid: true, stars: 3,
    });
  });

  it("ignores diagonals, jumps, repeated endpoints and revisits", () => {
    const state = [0, 1, 2, 5, 4].reduce(tryStep, createTrainingGame(params));
    for (const cell of [4, 0, 1, 6, 8, -1, 0.5]) expect(tryStep(state, cell)).toBe(state);
  });

  it("pops onto the previous cell and allows a removed checkpoint again", () => {
    const state = [0, 1, 2, 5].reduce(tryStep, createTrainingGame(params));
    const popped = tryStep(state, 2);
    expect(popped.path).toEqual([0, 1, 2]);
    expect(state.path).toEqual([0, 1, 2, 5]);
    expect(tryStep(popped, 5).path).toEqual(state.path);
  });

  it("truncates to visited cells and recomputes checkpoint order", () => {
    const state = [0, 1, 2, 5, 4, 3].reduce(tryStep, createTrainingGame(params));
    expect(truncateTo(state, 8)).toBe(state);
    expect(truncateTo(state, 3)).toBe(state);
    const truncated = truncateTo(state, 1);
    expect(truncated.path).toEqual([0, 1]);
    expect(tryStep(tryStep(truncated, 2), 5).path).toEqual([0, 1, 2, 5]);
    expect(truncateTo(state, 0).path).toEqual([0]);
    expect(state.path).toHaveLength(6);
  });

  it("blocks checkpoints out of order and requires the final checkpoint at the end", () => {
    const config = { ...params, checkpoints: [
      { cell: 0, k: 1 }, { cell: 8, k: 2 }, { cell: 1, k: 3 },
    ] };
    const state = tryStep(createTrainingGame(config), 0);
    expect(tryStep(state, 1)).toBe(state);
    const earlyEnd = { ...params, checkpoints: [{ cell: 0, k: 1 }, { cell: 1, k: 2 }] };
    expect(isSolved(solution.reduce(tryStep, createTrainingGame(earlyEnd)))).toBe(false);
  });

  it.each([5, 6])("uses strict scaled star boundaries for n=%i", (n) => {
    const fast = 12000 * n * n / 25;
    const medium = 25000 * n * n / 25;
    expect(starsFor(n, 0)).toBe(3);
    expect(starsFor(n, fast - 1)).toBe(3);
    expect(starsFor(n, fast)).toBe(2);
    expect(starsFor(n, medium - 1)).toBe(2);
    expect(starsFor(n, medium)).toBe(1);
  });

  it.each([
    ["wrong_length", solution.slice(1)],
    ["out_of_bounds", [0, 1, 2, 5, 4, 3, 6, 9, 8]],
    ["out_of_bounds", [0, 1, 2, 5, 4, 3, 6, 0.5, 8]],
    ["revisit", [0, 1, 2, 5, 4, 3, 6, 0, 8]],
    ["bad_start", [1, 0, 2, 5, 4, 3, 6, 7, 8]],
    ["bad_end", [0, 1, 2, 5, 4, 3, 6, 8, 7]],
    ["not_adjacent", [0, 2, 1, 5, 4, 3, 6, 7, 8]],
  ] as const)("rejects %s", (reason, path) => {
    expect(verifyTraining(params, { path, elapsed_ms: 0 })).toEqual({ valid: false, reason });
  });

  it("rejects checkpoint order even when the path is otherwise Hamiltonian", () => {
    const config = { ...params, checkpoints: [
      { cell: 0, k: 1 }, { cell: 4, k: 2 }, { cell: 5, k: 3 }, { cell: 8, k: 4 },
    ] };
    expect(verifyTraining(config, { path: solution, elapsed_ms: 0 })).toEqual({
      valid: false, reason: "checkpoint_order",
    });
  });

  it("rejects invalid elapsed time", () => {
    for (const elapsed_ms of [-1, NaN, Infinity]) {
      expect(verifyTraining(params, { path: solution, elapsed_ms })).toEqual({
        valid: false, reason: "non_monotonic_time",
      });
    }
  });

  it("accepts any correct path, with unsorted checkpoint metadata", () => {
    const config = { ...params, checkpoints: [{ cell: 8, k: 2 }, { cell: 0, k: 1 }] };
    for (const path of [solution, [0, 3, 6, 7, 4, 1, 2, 5, 8]]) {
      expect(verifyTraining(config, { path, elapsed_ms: 10000 })).toEqual({ valid: true, stars: 1 });
    }
  });
});
