import { describe, expect, it } from "vitest";
import { decodedBehaviour, odourBehaviour, sitePosition } from "./vial";

describe("authoritative vial display", () => {
  it("selects only a finite decoder label", () => {
    expect(decodedBehaviour({ walk: 0.2, avoid: 0.7, surprise: 100, feed: NaN })).toBe("avoid");
    expect(decodedBehaviour(null)).toBe("rest");
  });
  it("shows measured odour choices without inventing an outcome", () => {
    expect(odourBehaviour({ toward: 1, away: 0 })).toBe("approach");
    expect(odourBehaviour({ toward: 0, away: 1 })).toBe("avoid");
    expect(odourBehaviour({ toward: 4, away: 4 })).toBe("rest");
    expect(odourBehaviour({ toward: NaN, away: 0 })).toBeUndefined();
  });
  it("rejects invalid positions", () => {
    expect(sitePosition([1, NaN, 2])).toEqual([0.24, -0.05, 0.94]);
  });
});
