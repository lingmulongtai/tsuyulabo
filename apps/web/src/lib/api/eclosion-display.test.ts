import { expect, it } from "vitest";
import { eclosionOdds, eclosionResult } from "./eclosion-display";
import type { components } from "./schema";

const response: components["schemas"]["Eclosion"] = {
  tier: 2, omen_sequence: [0, 1, 2, 3, 2],
  adult: { id: "new-adult-id", name: "つゆ", sex: "f", strain: "wild", stars: 4, traits: ["brave", "keen_nose"], skills: {}, level: 1, preferences: {} },
};
it("maps the awarded adult and preserves fake-out omens without rerolling", () => {
  expect(eclosionResult(response)).toEqual({ tier: 2, omen_sequence: [0, 1, 2, 3, 2], adult: { name: "つゆ", sex: "f", strain: "wild", stars: 4, traits: ["brave", "keen_nose"] } });
  expect(response.adult.id).toBe("new-adult-id");
});
it("maps each tier and mutant strain", () => {
  for (const tier of [0, 1, 2, 3]) expect(eclosionResult({ ...response, tier }).tier).toBe(tier);
  expect(eclosionResult({ ...response, tier: 3, adult: { ...response.adult, strain: "white", sex: "m", stars: 5 } }).adult).toMatchObject({ strain: "white", sex: "m", stars: 5 });
});
it("rejects invalid animation indices", () => {
  for (const tier of [-1, 4, 1.5, NaN]) expect(() => eclosionResult({ ...response, tier })).toThrow();
  expect(() => eclosionResult({ ...response, omen_sequence: [0, 5] })).toThrow();
});
const odds = { normal: [72, 22, 5.5, 0.5], silver: [60, 30, 9, 1], gold: [40, 38, 18, 4], rainbow: [20, 40, 30, 10] };
it("reads published odds as percentages in tier order", () => {
  expect(eclosionOdds({ eclosion: odds, tiers: ["white", "blue", "gold", "rainbow"] })).toEqual(odds);
});
it("rejects missing or malformed odds instead of displaying demo values", () => {
  for (const value of [null, {}, { eclosion: { ...odds, gold: [1] } }, { eclosion: { ...odds, normal: [72, 22, 5.5, NaN] } }]) expect(() => eclosionOdds(value)).toThrow();
});
