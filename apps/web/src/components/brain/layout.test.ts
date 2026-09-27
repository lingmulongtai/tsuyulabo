import { describe, expect, it } from "vitest";
import { edgePath, edgeWidth, layoutGroups, rateGlow } from "./layout";
import type { ActivityGroup } from "./types";

const groups: ActivityGroup[] = [
  { name: "ORN", kind: "sensory", circuit: "olfaction_mb", rates: [0] },
  { name: "PN", kind: "inter", circuit: "olfaction_mb", rates: [0] },
  { name: "KC", kind: "inter", circuit: "olfaction_mb", rates: [0] },
  { name: "APL", kind: "inter", circuit: "olfaction_mb", rates: [0] },
  { name: "MBON_ap", kind: "output", circuit: "olfaction_mb", rates: [0] },
  { name: "PAM", kind: "modulatory", circuit: "olfaction_mb", rates: [0] },
  { name: "Gr64f", kind: "sensory", circuit: "feeding", rates: [0] },
  { name: "MN9", kind: "output", circuit: "feeding", rates: [0] },
];

describe("brain layout", () => {
  it("places sensory, interneuron and output columns with a separate DAN row", () => {
    const layout = layoutGroups(groups);
    const byName = Object.fromEntries(layout.nodes.map((node) => [node.name, node]));
    expect(byName.ORN.x).toBeLessThan(byName.PN.x);
    expect(byName.PN.x).toBeLessThan(byName.MBON_ap.x);
    expect(byName.PN.y).toBeLessThan(byName.KC.y);
    expect(byName.KC.y).toBeLessThan(byName.APL.y);
    expect(byName.PAM.y).toBeGreaterThan(byName.APL.y);
    expect(byName.Gr64f.y).toBeLessThan(byName.ORN.y);
    expect(new Set(layout.nodes.map(({ x, y }) => `${x},${y}`)).size).toBe(groups.length);
    expect(layout.nodes.every(({ x, y }) => x > 20 && x < layout.width - 20 && y > 20 && y < layout.height - 20)).toBe(true);
  });

  it("is deterministic without mutating API data", () => {
    const before = structuredClone(groups);
    expect(layoutGroups([...groups].reverse())).toEqual(layoutGroups(groups));
    expect(groups).toEqual(before);
    expect(layoutGroups([]).nodes).toEqual([]);
  });

  it("routes feedback edges separately and scales weights and rates with bounds", () => {
    const pre = { x: 360, y: 100 }, post = { x: 360, y: 200 };
    expect(edgePath(pre, post)).toContain("430");
    expect(edgePath(post, pre)).toContain("290");
    expect(edgeWidth(20)).toBe(edgeWidth(-20));
    expect(edgeWidth(100)).toBeGreaterThan(edgeWidth(1));
    expect(edgeWidth(1e20)).toBe(5);
    expect([rateGlow(-1), rateGlow(0), rateGlow(100), rateGlow(2000)]).toEqual([0, 0, 0.5, 1]);
  });
});
