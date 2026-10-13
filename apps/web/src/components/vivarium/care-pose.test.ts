import { describe, expect, it } from "vitest";
import { carePose } from "./care-pose";
import type { Point } from "./types";

const sites: Point[] = [[0.24, 0.55, 0.94], [-0.3, -1, 0.85], [0.2, 1.15, 0.94]];
describe("glass care poses", () => {
  it("points the larva's longitudinal Z axis up the wall with body clearance", () => {
    for (const site of sites) {
      const pose = carePose(site, 50);
      expect(-Math.sin(pose.rotation[0])).toBeCloseTo(1);
      expect(Math.hypot(pose.position[0], pose.position[2]) + 0.1).toBeLessThan(1.065);
      expect(pose.position[1] + 0.29).toBeLessThanOrEqual(1.12);
    }
    expect(carePose(sites[0], 30).position[1]).toBeGreaterThan(carePose(sites[0], 0).position[1]);
  });
  it("faces the emerging adult inward and retains clearance for unfolded wings", () => {
    for (const site of sites) for (const progress of [0.15, 0.5, 1]) {
      const pose = carePose(site, 0, progress);
      expect(Math.hypot(pose.position[0], pose.position[2]) + 0.62).toBeLessThan(1.065);
      expect(Math.sin(pose.rotation[1]) * site[0] + Math.cos(pose.rotation[1]) * site[2]).toBeLessThan(0);
    }
  });
});
