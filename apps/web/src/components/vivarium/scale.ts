import type { Point } from "./types";

/** Renderer units are millimetres. Public care/decoder coordinates remain unchanged. */
export const vialMM = { radius: 12.5, innerRadius: 11.8, height: 95, floor: 1.5, food: 21.5 } as const;
export const radialMM = vialMM.innerRadius / 1.065;
export const verticalMM = (vialMM.height - vialMM.food) / (1.59 + 1.075);
export function toMillimetres([x, y, z]: Point): [number, number, number] {
  return [x * radialMM, vialMM.food + (y + 1.075) * verticalMM, z * radialMM];
}
export function fromMillimetres([x, y, z]: Point): [number, number, number] {
  return [x / radialMM, (y - vialMM.food) / verticalMM - 1.075, z / radialMM];
}

// Independent, uniform anatomical scales; never stretch insects with the vial.
export const organismMM = { adult: 2.5 / (1.16 * 0.58), egg: 0.5 / 0.208, larva: 4 / 0.56, pupa: 3 / 0.439 } as const;
export function groundPosition(point: Point, kind: keyof typeof organismMM): [number, number, number] {
  const s = organismMM[kind];
  const clearance = { adult: 0.15 * 0.58, egg: 0.083, larva: 0.08, pupa: 0 }[kind] * s;
  return [point[0] * radialMM, vialMM.food + clearance + (point[1] + 0.99) * verticalMM, point[2] * radialMM];
}

/** Emerge from the case mouth with millimetre clearance, independent of legacy motor bounds. */
export function emergencePosition(site: Point, progress: number): [number, number, number] {
  const p = Math.max(0, Math.min(1, progress)), anchor = toMillimetres(site);
  const r = Math.max(0.001, Math.hypot(anchor[0], anchor[2]));
  return [anchor[0] + 0.3 - anchor[0] / r * p, anchor[1] + 2 + p * 0.6, anchor[2] + 0.2 - anchor[2] / r * p];
}
