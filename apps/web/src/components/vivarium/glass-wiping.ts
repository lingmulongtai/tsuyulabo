import type { Point, VivariumProps } from "./types";

/** Match the front-cylinder raycast UVs; rear droplets cannot be reached through glass. */
export function glassWiped([x, y, z]: Point, wiped: NonNullable<VivariumProps["wiped"]>): boolean {
  if (z < 0 || y < -1.11 || y > 1.15) return false;
  const u = (Math.atan2(x, z) + Math.PI / 2) / Math.PI;
  const v = (1.15 - y) / 2.26;
  return wiped.some(stamp => Math.hypot(stamp.u - u, stamp.v - v) <= 0.12);
}
