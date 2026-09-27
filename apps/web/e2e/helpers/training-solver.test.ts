import { describe, expect, it } from "vitest";
import day2 from "../../../../packages/fixtures/puzzles/training/day2_11999ms.json";
import day4 from "../../../../packages/fixtures/puzzles/training/day4_17279ms.json";
import { verifyTraining } from "../../src/game/puzzles/training";
import type { TrainingParams } from "../../src/game/puzzles/types";
import { solveTraining } from "./training-solver";

describe("training solver", () => {
  for (const fixture of [day2, day4]) {
    for (let rotation = 0; rotation < 4; rotation++) {
      for (const reflect of [false, true]) {
        it(`solves ${fixture.params.n}x${fixture.params.n}, rotation ${rotation}, reflect ${reflect}`, () => {
          const n = fixture.params.n;
          const params: TrainingParams = {
            ...fixture.params, cue: "banana", valence: "reward",
            checkpoints: fixture.params.checkpoints.map(cp => {
              let r = Math.floor(cp.cell / n), c = cp.cell % n;
              if (reflect) c = n - 1 - c;
              for (let i = 0; i < rotation; i++) [r, c] = [c, n - 1 - r];
              return { ...cp, cell: r * n + c };
            }).reverse(), // The wire order need not be sorted by k.
          };
          const path = solveTraining(params);
          expect(verifyTraining(params, { path, elapsed_ms: 5000 }).valid).toBe(true);
        });
      }
    }
  }

  it("rejects impossible endpoints without returning a partial path", () => {
    expect(() => solveTraining({ n: 5, checkpoints: [{ cell: 0, k: 1 }, { cell: 1, k: 2 }] }))
      .toThrow("No training solution");
  });

  it("rejects repeated checkpoints", () => {
    expect(() => solveTraining({ n: 5, checkpoints: [{ cell: 0, k: 1 }, { cell: 0, k: 2 }] }))
      .toThrow("Invalid training checkpoints");
  });
});
