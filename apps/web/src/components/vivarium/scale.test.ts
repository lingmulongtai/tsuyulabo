import { describe, expect, it } from "vitest";
import { emergencePosition, fromMillimetres, groundPosition, organismMM, toMillimetres, vialMM } from "./scale";

describe("millimetre scene and legacy care contract", () => {
  it("preserves food, rim and radius anchors", () => {
    expect(toMillimetres([1.065, -1.075, 0])).toEqual([11.8, 21.5, 0]);
    expect(toMillimetres([0, 1.59, 0])[1]).toBe(95);
    expect(vialMM.food - vialMM.floor).toBe(20);
    expect(1.16 * 0.58 * organismMM.adult / (2 * vialMM.radius)).toBeCloseTo(0.1);
  });
  it("round trips saved sites and picks without changing API units", () => {
    for (const p of [[0.24, 0.55, 0.94], [0, -1, 1], [0.2, 1.15, 0.8]] as const) {
      fromMillimetres(toMillimetres(p)).forEach((v, i) => expect(v).toBeCloseTo(p[i], 12));
    }
  });
  it("places feet on food and preserves flight/burrow displacement", () => {
    const grounded = groundPosition([0, -0.99, 0], "adult");
    expect(grounded[1] - 0.15 * 0.58 * organismMM.adult).toBe(vialMM.food);
    expect(groundPosition([0, -0.49, 0], "adult")[1]).toBeGreaterThan(grounded[1]);
    expect(groundPosition([0, -1.09, 0], "larva")[1]).toBeLessThan(vialMM.food);
  });
});

it("keeps the emerging adult within one body length of the pupal mouth", () => {
  const site = [0.24, -0.05, 0.94] as const, anchor = toMillimetres(site);
  for (const p of [0, 0.15, 0.5, 1]) {
    const position = emergencePosition(site, p);
    expect(Math.hypot(position[0] - anchor[0], position[2] - anchor[2])).toBeLessThan(1.5);
    expect(position[1] - anchor[1]).toBeGreaterThanOrEqual(2);
    expect(position[1] - anchor[1]).toBeLessThanOrEqual(3);
  }
});
