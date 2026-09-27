import { describe, expect, it } from "vitest";
import { gradeTap, markerPosition, verifyCleaning } from "./cleaning";
import type { CleaningParams } from "./types";

const params: CleaningParams = {
  period_ms: 1000, taps: 3, zone: { center: 0.5, perfect: 0.06, good: 0.15 }, phase: 0,
};

describe("cleaning", () => {
  it.each([[0, 0], [250, 0.5], [500, 1], [750, 0.5], [1000, 0], [1250, 0.5]])(
    "computes the triangle wave at %i ms", (time, position) => {
      expect(markerPosition(params, time)).toBe(position);
    },
  );

  it("applies phase and repeats after each period", () => {
    const config = { ...params, phase: 0.27, period_ms: 1400 };
    expect(markerPosition(config, 0)).toBeCloseTo(0.54);
    expect(markerPosition(config, 1400)).toBeCloseTo(0.54);
    expect(markerPosition({ ...params, phase: -0.25 }, 0)).toBe(0.5);
  });

  it("includes both grade boundaries on both halves of the wave", () => {
    const config = { ...params, zone: { center: 0.5, perfect: 0.125, good: 0.25 } };
    for (const t of [187.5, 312.5, 687.5, 812.5]) expect(gradeTap(config, t)).toBe("perfect");
    for (const t of [125, 375, 625, 875]) expect(gradeTap(config, t)).toBe("good");
    expect(gradeTap(config, 124)).toBe("miss");
    expect(gradeTap(config, 313)).toBe("good");
  });

  it("sums mixed grades and caps three perfects at 100", () => {
    expect(verifyCleaning(params, { taps: [250, 800, 1000], elapsed_ms: 1000 })).toEqual({
      valid: true, score: 61, grades: ["perfect", "good", "miss"],
    });
    expect(verifyCleaning(params, { taps: [250, 750, 1250], elapsed_ms: 1250 })).toEqual({
      valid: true, score: 100, grades: ["perfect", "perfect", "perfect"],
    });
  });

  it.each([
    ["wrong_tap_count", [1, 2]],
    ["wrong_tap_count", [1, 2, 3, 4]],
    ["non_monotonic_time", [1, 1, 2]],
    ["non_monotonic_time", [2, 1, 3]],
    ["non_monotonic_time", [-1, 1, 2]],
    ["non_monotonic_time", [1, 2, NaN]],
    ["non_monotonic_time", [1, 2, Infinity]],
    ["non_monotonic_time", [1, 2, 3.5]],
    ["time_exceeded", [1, 2, 10001]],
  ] as const)("rejects %s", (reason, taps) => {
    expect(verifyCleaning(params, { taps, elapsed_ms: 11000 })).toEqual({ valid: false, reason });
  });

  it("accepts a tap at zero and at 10000 ms, with later submission delivery", () => {
    expect(verifyCleaning(params, { taps: [0, 500, 10000], elapsed_ms: 11000 }).valid).toBe(true);
  });

  it("requires finite elapsed time at or after the last tap", () => {
    for (const elapsed_ms of [-1, 2, 3.5, NaN, Infinity]) {
      expect(verifyCleaning(params, { taps: [1, 2, 3], elapsed_ms })).toEqual({
        valid: false, reason: "non_monotonic_time",
      });
    }
  });

  it("limits elapsed time after tap count but before tap validation", () => {
    expect(verifyCleaning(params, { taps: [0, 500, 10000], elapsed_ms: 600000 }).valid)
      .toBe(true);
    expect(verifyCleaning(params, { taps: [-1, 1, 2], elapsed_ms: 600001 }))
      .toEqual({ valid: false, reason: "time_exceeded" });
    expect(verifyCleaning(params, { taps: [], elapsed_ms: 600001 }))
      .toEqual({ valid: false, reason: "wrong_tap_count" });
  });

  it("tolerates boundary float error without widening zones beyond epsilon", () => {
    for (const t of [220, 280, 720, 780]) expect(gradeTap(params, t)).toBe("perfect");
    for (const t of [175, 325, 675, 825]) expect(gradeTap(params, t)).toBe("good");
    expect(gradeTap(params, 280 + 1e-8)).toBe("good");
    expect(gradeTap(params, 325 + 1e-8)).toBe("miss");
  });
});
