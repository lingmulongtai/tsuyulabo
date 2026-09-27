import type { CleaningParams, CleaningSubmission, CleaningVerifyResult, Grade } from "./types";
import { timesReason } from "./timing";

export function markerPosition(params: CleaningParams, tMs: number): number {
  const remainder = (tMs / params.period_ms + params.phase) % 1;
  const u = remainder < 0 ? remainder + 1 : remainder;
  return u < 0.5 ? 2 * u : 2 - 2 * u;
}

export function gradeTap(params: CleaningParams, tMs: number): Grade {
  const d = Math.abs(markerPosition(params, tMs) - params.zone.center);
  return d <= params.zone.perfect + 1e-12 ? "perfect"
    : d <= params.zone.good + 1e-12 ? "good" : "miss";
}

export function verifyCleaning(
  params: CleaningParams, submission: CleaningSubmission,
): CleaningVerifyResult {
  if (!Array.isArray(submission.taps) || submission.taps.length !== params.taps) {
    return { valid: false, reason: "wrong_tap_count" };
  }
  const reason = timesReason(submission.taps, submission.elapsed_ms, true, 10000);
  if (reason) return { valid: false, reason };
  const grades = submission.taps.map((t) => gradeTap(params, t));
  const points: Record<Grade, number> = { perfect: 34, good: 22, miss: 5 };
  return { valid: true, score: Math.min(100, grades.reduce((sum, g) => sum + points[g], 0)), grades };
}
