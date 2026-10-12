import type { Quality } from "./types";
export const budgets = {
  high: { dpr: 1.75, hairs: 420, droplets: 110, shadows: true, post: true, ao: true },
  medium: { dpr: 1.25, hairs: 180, droplets: 48, shadows: true, post: true, ao: false },
  low: { dpr: 1, hairs: 65, droplets: 16, shadows: false, post: false, ao: false },
} as const;
export function initialQuality(device: { cores?: number; memory?: number; mobile?: boolean; renderer?: string }): Quality {
  if (/swiftshader|llvmpipe|software/i.test(device.renderer ?? "") || (device.cores ?? 4) <= 2 || (device.memory ?? 4) <= 2) return "low";
  return device.mobile || (device.cores ?? 4) < 8 || (device.memory ?? 4) < 8 ? "medium" : "high";
}
/** Slow frames sustained over 3 seconds downgrade; no oscillation or hidden-tab penalty. */
export class QualityMonitor {
  private elapsed = 0;
  private frames = 0;
  private warmup = 2;
  sample(dt: number, current: Quality, automatic: boolean): Quality {
    if (!automatic || dt <= 0 || dt > 2 || !Number.isFinite(dt)) return current;
    if (this.warmup > 0) { this.warmup -= dt; return current; }
    this.elapsed += dt; this.frames++;
    if (this.elapsed < 3) return current;
    const fps = this.frames / this.elapsed;
    this.elapsed = 0; this.frames = 0;
    if (fps < 48 && current !== "low") { this.warmup = 2; return current === "high" ? "medium" : "low"; }
    return current;
  }
}
