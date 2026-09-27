import { describe, expect, it } from "vitest";
import { createMealGame, place, verifyMeal } from "../../src/game/puzzles/meal";
import { verifyCleaning } from "../../src/game/puzzles/cleaning";
import { verifyTemperature } from "../../src/game/puzzles/temperature";
import { cleaningTimes, hintedSite, nextMealMove, temperatureTime } from "./capture-solvers";

describe("media care solvers", () => {
  it("makes legal placements and clears lines across multiple hands", () => {
    const params = { rows: 8, cols: 8, hand_size: 3, time_limit_ms: 30000,
      theme: "banana" as const,
      pieces: Array.from({ length: 45 }, () => ({ shape: "o4" as const, ingredient: "banana" as const })) };
    let state = createMealGame(params);
    for (let i = 0; i < 45; i++) {
      const move = nextMealMove(state);
      expect(move).toBeDefined();
      state = place(state, move!.p, move!.r, move!.c, 0).state;
    }
    expect(state.lines).toBeGreaterThan(10);
    expect(verifyMeal(params, { moves: state.moves, elapsed_ms: 30000 })).toMatchObject({ valid: true, score: state.score });
  });

  it("hits perfect timing for every daily period across random phases", () => {
    for (let phase = 0; phase < 1; phase += 0.017) {
      for (const period_ms of [1100, 1200, 1300, 1400]) {
        const params = { period_ms, phase, taps: 3, zone: { center: 0.5, perfect: 0.06, good: 0.15 } };
        const taps = cleaningTimes(params);
        expect(verifyCleaning(params, { taps, elapsed_ms: taps[2] })).toMatchObject({
          valid: true, score: 100, grades: ["perfect", "perfect", "perfect"],
        });
      }
      const params = { period_ms: 1600, phase, center_c: 25, amp_c: 7 };
      const stop_ms = temperatureTime(params);
      expect(verifyTemperature(params, { stop_ms, elapsed_ms: stop_ms })).toMatchObject({ valid: true, grade: "perfect" });
    }
  });

  it("matches the public hint after the options are shuffled", () => {
    expect(hintedSite({ hint: "えさから離れた乾いた場所を探してみよう。", options: [
      { id: "a", label: "えさのそば", detail: "しっとりしている" },
      { id: "c", label: "壁の乾いたところ", detail: "えさから離れている" },
    ] }).id).toBe("c");
  });
});
