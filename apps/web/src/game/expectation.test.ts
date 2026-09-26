import { expect, it } from "vitest";
import { TIERS, tierForIndex, tierForRank } from "./expectation";

it("exposes the ordered shared expectation tokens", () => {
  expect(TIERS).toEqual([
    { id: "white", label: "白", color: "#FFFFFF" },
    { id: "blue", label: "青", color: "#7FC8FF" },
    { id: "gold", label: "金", color: "#FFD54A" },
    { id: "rainbow", label: "虹", color: "rainbow" },
  ]);
});

it("maps all week ranks to their display tiers", () => {
  for (const [i, rank] of (["normal", "silver", "gold", "rainbow"] as const).entries()) {
    expect(tierForRank(rank)).toBe(TIERS[i]);
    expect(tierForIndex(i)).toBe(TIERS[i]);
  }
});

it("handles intermediate and invalid animation indices predictably", () => {
  expect(tierForIndex(1.9)).toBe(TIERS[1]);
  expect(tierForIndex(100)).toBe(TIERS[3]);
  for (const index of [-1, NaN, Infinity, -Infinity]) expect(tierForIndex(index)).toBe(TIERS[0]);
});
