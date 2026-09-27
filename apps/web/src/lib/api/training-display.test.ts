import { expect, it } from "vitest";
import { ApiError } from "./client";
import { canPracticeOffline, trainingOutcome } from "./training-display";

const result = { stars: 2, hirameki: true, association: { cue: "banana", valence: "reward", value: 0.72 }, skill_unlocked: "banana_search" };
it("uses server stars, insight, learned preference and unlocked skill", () => {
  expect(trainingOutcome(result)).toEqual({ stars: 2, hirameki: true, association: result.association, skillUnlocked: "banana_search" });
});
it("preserves negative and boundary preferences", () => {
  for (const value of [-1, -0.52, 0, 1]) {
    expect(trainingOutcome({ ...result, association: { cue: "blue_light", valence: "punish", value }, skill_unlocked: null }).association?.value).toBe(value);
  }
});
it("keeps queued learning pending instead of inventing a preference", () => {
  expect(trainingOutcome({ ...result, association: null, skill_unlocked: null })).toMatchObject({ association: null, skillUnlocked: null });
});
it("rejects incompatible responses", () => {
  for (const value of [null, {}, { ...result, stars: 5 }, { ...result, hirameki: 1 }, { ...result, association: { ...result.association, value: NaN } }, { ...result, association: { ...result.association, value: 2 } }]) {
    expect(() => trainingOutcome(value)).toThrow(ApiError);
  }
});
it("offers offline practice only for connectivity or server failures", () => {
  expect(canPracticeOffline(new ApiError(0, "offline", ""))).toBe(true);
  expect(canPracticeOffline(new ApiError(503, "unavailable", ""))).toBe(true);
  expect(canPracticeOffline(new ApiError(409, "daily_limit_reached", ""))).toBe(false);
  expect(canPracticeOffline(new ApiError(502, "invalid_response", ""))).toBe(false);
});
