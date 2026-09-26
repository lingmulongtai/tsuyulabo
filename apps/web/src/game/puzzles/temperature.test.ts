import { describe, expect, it } from "vitest";
import { needleTemp, scoreTemperature, verifyTemperature } from "./temperature";
import type { TemperatureParams } from "./types";

const params: TemperatureParams = { period_ms: 1600, center_c: 25, amp_c: 7, phase: 0 };

describe("temperature", () => {
  it.each([[0, 25], [400, 32], [800, 25], [1200, 18], [1600, 25]])(
    "computes the sine wave at %i ms", (time, temp) => {
      expect(needleTemp(params, time)).toBeCloseTo(temp);
    },
  );

  it("uses center, amplitude and phase from params", () => {
    expect(needleTemp({ ...params, center_c: 23, amp_c: 4, phase: 0.25 }, 0)).toBe(27);
    expect(scoreTemperature({ ...params, center_c: 23, amp_c: 0 }, 0)).toEqual({
      score: 60, grade: "good",
    });
  });

  it.each([
    [25, 100, "perfect"], [25.5, 90, "perfect"], [25.55, 89, "good"],
    [27, 60, "good"], [27.05, 59, "miss"], [32, 0, "miss"], [18, 0, "miss"],
    [25.125, 98, "perfect"], [25.375, 92, "perfect"], [24.625, 92, "perfect"],
  ] as const)("scores %f degrees", (center_c, score, grade) => {
    expect(scoreTemperature({ ...params, center_c, amp_c: 0 }, 0)).toEqual({ score, grade });
  });

  it("verifies the stop, permitting later delivery and no invented time limit", () => {
    expect(verifyTemperature(params, { stop_ms: 0, elapsed_ms: 0 })).toEqual({
      valid: true, score: 100, grade: "perfect",
    });
    expect(verifyTemperature(params, { stop_ms: 16000, elapsed_ms: 20000 }).valid).toBe(true);
    expect(verifyTemperature(params, { stop_ms: 400, elapsed_ms: 400 })).toEqual({
      valid: true, score: 0, grade: "miss",
    });
  });

  it.each([
    [-1, 0], [2, 1], [0, -1], [NaN, 0], [0, NaN], [Infinity, Infinity], [0, Infinity],
  ])("rejects invalid stop/elapsed time %s/%s", (stop_ms, elapsed_ms) => {
    expect(verifyTemperature(params, { stop_ms, elapsed_ms })).toEqual({
      valid: false, reason: "non_monotonic_time",
    });
  });
});
