import type { CleaningParams, CleaningSubmission, CleaningVerifyResult, Grade } from "./types";

export function markerPosition(params: CleaningParams, tMs: number): number {
  const remainder = (tMs / params.period_ms + params.phase) % 1;
  const u = remainder < 0 ? remainder + 1 : remainder;
  return u < 0.5 ? 2 * u : 2 - 2 * u;
}

export function gradeTap(params: CleaningParams, tMs: number): Grade {
  const d = Math.abs(markerPosition(params, tMs) - params.zone.center);
  return d <= params.zone.perfect ? "perfect" : d <= params.zone.good ? "good" : "miss";
}

export function verifyCleaning(
  params: CleaningParams, submission: CleaningSubmission,
): CleaningVerifyResult {
  if (submission.taps.length !== params.taps) return { valid: false, reason: "wrong_tap_count" };
  if (!Number.isFinite(submission.elapsed_ms) || submission.elapsed_ms < 0) {
    return { valid: false, reason: "non_monotonic_time" };
  }
  let previous: number | undefined;
  for (const t of submission.taps) {
    if (!Number.isFinite(t) || t < 0 || (previous !== undefined && t <= previous)) {
      return { valid: false, reason: "non_monotonic_time" };
    }
    if (t > 10000) return { valid: false, reason: "time_exceeded" };
    previous = t;
  }
  if (submission.elapsed_ms < (previous ?? 0)) {
    return { valid: false, reason: "non_monotonic_time" };
  }
  const grades = submission.taps.map((t) => gradeTap(params, t));
  const points: Record<Grade, number> = { perfect: 34, good: 22, miss: 5 };
  return { valid: true, score: Math.min(100, grades.reduce((sum, g) => sum + points[g], 0)), grades };
}
