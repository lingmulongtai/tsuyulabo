import { timesReason } from "./timing";
import type {
  TemperatureParams, TemperatureScore, TemperatureSubmission, TemperatureVerifyResult,
} from "./types";

export function needleTemp(params: TemperatureParams, tMs: number): number {
  return params.center_c + params.amp_c * Math.sin(2 * Math.PI * (tMs / params.period_ms + params.phase));
}

export function scoreTemperature(params: TemperatureParams, stopMs: number): TemperatureScore {
  const rawScore = 100 - Math.abs(needleTemp(params, stopMs) - 25) * 20;
  const score = Math.max(0, Math.floor(rawScore + 0.5));
  return { score, grade: score >= 90 ? "perfect" : score >= 60 ? "good" : "miss" };
}

export function verifyTemperature(
  params: TemperatureParams, submission: TemperatureSubmission,
): TemperatureVerifyResult {
  const { stop_ms, elapsed_ms } = submission;
  const reason = timesReason([stop_ms], elapsed_ms);
  if (reason) return { valid: false, reason };
  return { valid: true, ...scoreTemperature(params, stop_ms) };
}
