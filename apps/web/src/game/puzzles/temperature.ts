import type {
  TemperatureParams, TemperatureScore, TemperatureSubmission, TemperatureVerifyResult,
} from "./types";

export function needleTemp(params: TemperatureParams, tMs: number): number {
  return params.center_c + params.amp_c * Math.sin(2 * Math.PI * (tMs / params.period_ms + params.phase));
}

/** Match the Python server's round(): exact half ties go to the even integer. */
function roundEven(value: number): number {
  const lower = Math.floor(value);
  return value - lower === 0.5 ? lower + (lower % 2 === 0 ? 0 : 1) : Math.round(value);
}

export function scoreTemperature(params: TemperatureParams, stopMs: number): TemperatureScore {
  const score = Math.max(0, roundEven(100 - Math.abs(needleTemp(params, stopMs) - 25) * 20));
  return { score, grade: score >= 90 ? "perfect" : score >= 60 ? "good" : "miss" };
}

export function verifyTemperature(
  params: TemperatureParams, submission: TemperatureSubmission,
): TemperatureVerifyResult {
  const { stop_ms, elapsed_ms } = submission;
  if (!Number.isFinite(stop_ms) || !Number.isFinite(elapsed_ms) || stop_ms < 0 || elapsed_ms < stop_ms) {
    return { valid: false, reason: "non_monotonic_time" };
  }
  // The spec places no maximum on stop_ms (unlike meal and cleaning).
  return { valid: true, ...scoreTemperature(params, stop_ms) };
}
