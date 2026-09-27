import type { InvalidReason } from "./types";

/** Match domain/puzzles/common.py, including the order of competing errors. */
export function timesReason(
  times: readonly number[], elapsed: number, strict = false, limit = 600000,
): InvalidReason | null {
  if (!Number.isInteger(elapsed) || elapsed < 0) return "non_monotonic_time";
  if (elapsed > 600000) return "time_exceeded";
  let previous = -1;
  for (const value of times) {
    if (!Number.isInteger(value) || value < 0 || value < previous ||
      (strict && value === previous)) return "non_monotonic_time";
    if (value > limit) return "time_exceeded";
    previous = value;
  }
  return previous > elapsed ? "non_monotonic_time" : null;
}
