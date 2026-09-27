import { expect, it } from "vitest";
import { behaviorProbabilities } from "./behavior-display";

it("preserves decoder probabilities including zeroes for the supported animations", () => {
  const probabilities = { rest: 0.1, walk: 0.1, turn_left: 0.1, turn_right: 0.1, feed: 0, escape: 0, groom: 0.6, approach: 0, avoid: 0 };
  expect(behaviorProbabilities(probabilities)).toEqual(probabilities);
});
it("omits unknown behaviours rather than creating unsupported animation classes", () => {
  expect(behaviorProbabilities({ walk: 0.7, future_behavior: 0.3 })).toEqual({ walk: 0.7 });
});
it("rejects invalid probabilities and empty observations", () => {
  const invalid: Record<string, number>[] = [{}, { rest: 0 }, { rest: -1 }, { rest: NaN }, { rest: Infinity }, { rest: 2 }, { unknown: 1 }];
  for (const data of invalid) {
    expect(() => behaviorProbabilities(data)).toThrow();
  }
});
