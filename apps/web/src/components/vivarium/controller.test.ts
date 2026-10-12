import { describe, expect, it } from "vitest";
import { BehaviourController } from "./controller";
import { displayStage } from "./types";

const advance = (controller: BehaviourController, seconds = 2) => {
  for (let i = 0; i < seconds * 60; i++) controller.update(1 / 60, "adult");
  return controller.pose;
};
describe("decoder motor controller", () => {
  it("reproduces an individual but varies different individuals", () => {
    const a = new BehaviourController("a"), b = new BehaviourController("a"), c = new BehaviourController("c");
    for (const x of [a, b, c]) { x.setBehaviour("walk"); advance(x, 5); }
    expect(a.pose).toEqual(b.pose);
    expect(a.pose.position).not.toEqual(c.pose.position);
  });
  it("approaches and avoids the supplied odour source", () => {
    for (const action of ["approach", "avoid"] as const) {
      const c = new BehaviourController(); c.pointOfInterest([0, -1, 0.7]); c.setBehaviour(action);
      const before = Math.hypot(c.pose.position[0], c.pose.position[2] - 0.7);
      advance(c, 3);
      const after = Math.hypot(c.pose.position[0], c.pose.position[2] - 0.7);
      expect(action === "approach" ? after < before : after > before).toBe(true);
    }
  });
  it("contains even escape trajectories and clamps suspended-tab deltas", () => {
    const c = new BehaviourController(); c.setBehaviour("escape");
    for (let i = 0; i < 3000; i++) c.update(i === 0 ? 100 : 1 / 60, "adult");
    expect(Math.hypot(c.pose.position[0], c.pose.position[2])).toBeLessThanOrEqual(0.491);
    expect(c.pose.position[1]).toBeLessThan(0.2);
  });
  it("blends feed and grooming then settles at rest", () => {
    const c = new BehaviourController(); c.setBehaviour("groom"); advance(c);
    expect(c.pose.groom).toBeGreaterThan(0.99);
    c.setBehaviour("feed"); advance(c); expect(c.pose.feed).toBeGreaterThan(0.99);
    c.setBehaviour("walk"); advance(c); c.setBehaviour("stop"); advance(c);
    expect(c.pose.speed).toBeLessThan(0.001); expect(c.pose.feed).toBeLessThan(0.001);
  });
  it("keeps eggs and pupae stationary and reduces motion", () => {
    const c = new BehaviourController(); c.setBehaviour("fly");
    const before = structuredClone(c.pose); c.update(1, "egg"); c.update(1, "pupa");
    expect(c.pose).toEqual(before);
    const a = new BehaviourController(), b = new BehaviourController();
    a.setBehaviour("walk"); b.setBehaviour("walk");
    for (let i = 0; i < 60; i++) { a.update(1 / 60, "adult"); b.update(1 / 60, "adult", true); }
    expect(b.pose.phase).toBeLessThan(a.pose.phase);
    expect(displayStage("wandering")).toBe("larva");
  });
  it("turns in opposite directions and burrows only as a larva", () => {
    const a = new BehaviourController(), b = new BehaviourController();
    a.setBehaviour("turn_left"); b.setBehaviour("turn_right"); advance(a); advance(b);
    expect(a.pose.heading).toBeGreaterThan(b.pose.heading);
    a.setBehaviour("burrow");
    for (let i = 0; i < 120; i++) a.update(1 / 60, "larva2");
    expect(a.pose.position[1]).toBeLessThan(-1.08);
  });
  it("keeps vestigial escape on the ground", () => {
    const c = new BehaviourController(); c.setBehaviour("escape");
    for (let i = 0; i < 300; i++) c.update(1 / 60, "adult", false, false);
    expect(c.pose.flight).toBe(0); expect(c.pose.speed).toBeGreaterThan(0);
  });
});
