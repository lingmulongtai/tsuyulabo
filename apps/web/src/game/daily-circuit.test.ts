import { describe, expect, it } from "vitest";
import { dailyElapsed, dailyTime } from "./daily-circuit";
import { createTrainingGame, isSolved, tryStep, verifyTraining } from "./puzzles/training";
import type { TrainingParams } from "./puzzles/types";

describe("daily circuit", () => {
  it("uses elapsed server time when resuming and keeps counting through a path reset", () => {
    const started = "2026-09-27T04:00:00+09:00";
    const server = "2026-09-26T19:00:12Z";
    expect(dailyElapsed(started, server, 300, 1300)).toBe(13000);
    expect(dailyElapsed(started, server, 300, 7300)).toBe(19000);
    expect(dailyTime(20123)).toBe("20.12秒");
  });

  it("plays all 49 cells and 9 checkpoints with the existing training engine", () => {
    const path = Array.from({ length: 49 }, (_, index) => {
      const row = Math.floor(index / 7), col = index % 7;
      return row * 7 + (row % 2 ? 6 - col : col);
    });
    const params: TrainingParams = {
      n: 7, cue: "banana", valence: "reward",
      checkpoints: Array.from({ length: 9 }, (_, i) => ({ cell: path[i * 6], k: i + 1 })),
    };
    let state = createTrainingGame(params);
    for (const cell of path) state = tryStep(state, cell);
    expect(isSolved(state)).toBe(true);
    expect(verifyTraining(params, { path, elapsed_ms: 20000 }).valid).toBe(true);
    expect(verifyTraining(params, { path: [...path.slice(0, 48), path[0]], elapsed_ms: 1 }).valid).toBe(false);
  });
});
