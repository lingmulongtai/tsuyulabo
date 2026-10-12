import { describe, expect, it } from "vitest";
import { initialQuality, QualityMonitor } from "./quality";
import type { Quality } from "./types";
describe("quality budget", () => {
  it("starts conservatively on phones, unknown devices and software renderers", () => {
    expect(initialQuality({})).toBe("medium");
    expect(initialQuality({ cores: 12, memory: 8, mobile: true })).toBe("medium");
    expect(initialQuality({ cores: 16, memory: 16 })).toBe("high");
    expect(initialQuality({ renderer: "ANGLE SwiftShader", cores: 16 })).toBe("low");
    expect(initialQuality({ memory: 2 })).toBe("low");
  });
  it("downgrades sustained slow frames but preserves explicit overrides", () => {
    const m = new QualityMonitor(); let q: Quality = "high";
    for (let i = 0; i < 200; i++) q = m.sample(1 / 30, q, true);
    expect(q).toBe("medium");
    for (let i = 0; i < 300; i++) q = m.sample(1 / 30, q, false);
    expect(q).toBe("medium");
  });
  it("does not penalize fast frames or tab suspension", () => {
    const m = new QualityMonitor(); let q: Quality = "high";
    for (let i = 0; i < 600; i++) { q = m.sample(1 / 60, q, true); q = m.sample(10, q, true); }
    expect(q).toBe("high");
  });
  it("downgrades extremely slow renderers rather than discarding their frames", () => {
    const m = new QualityMonitor(); let q: Quality = "medium";
    for (let i = 0; i < 25; i++) q = m.sample(0.3, q, true);
    expect(q).toBe("low");
  });
});
