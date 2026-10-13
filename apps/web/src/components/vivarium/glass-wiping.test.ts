import { describe, expect, it } from "vitest";
import { glassWiped } from "./glass-wiping";

describe("glass wiping", () => {
  it("erases front droplets at the same cylindrical UVs as the mask", () => {
    const stamps = [{ u: 0.5, v: 0.5 }];
    expect(glassWiped([0, 0.02, 1.058], stamps)).toBe(true);
    expect(glassWiped([0.1, 0.03, 1.05], stamps)).toBe(true);
    expect(glassWiped([1.058, 0.02, 0], stamps)).toBe(false);
    expect(glassWiped([0, 1, 1.058], stamps)).toBe(false);
  });
  it("leaves the rear, rim and untouched glass intact", () => {
    expect(glassWiped([0, 0.02, -1.058], [{ u: 0.5, v: 0.5 }])).toBe(false);
    expect(glassWiped([0, 1.3, 1.058], [{ u: 0.5, v: 0 }])).toBe(false);
    expect(glassWiped([0, 0.02, 1.058], [])).toBe(false);
  });
});
