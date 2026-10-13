import type { Point } from "./types";

/** Keep the complete organism inside the wall, not just its centre. */
export function carePose(site: Point, phase: number, emergence?: number) {
  const [x, y, z] = site;
  const radius = Math.hypot(x, z);
  const progress = Math.max(0, Math.min(1, emergence ?? 0));
  // Adults need the same wing/body clearance as the free-moving controller.
  const budget = emergence === undefined ? 0.94 : 0.42 - progress * 0.15;
  const scale = radius > budget ? budget / radius : 1;
  return {
    position: [x * scale, emergence === undefined ? Math.min(y, 0.82, -0.78 + phase * 0.035) : Math.min(0.82, y + progress * 0.25), z * scale] as [number, number, number],
    // Larvae are modelled along local Z. Adults emerge facing toward the centre.
    rotation: emergence === undefined ? [-Math.PI / 2, 0, 0] : [0, Math.atan2(-x, -z), 0],
  };
}
