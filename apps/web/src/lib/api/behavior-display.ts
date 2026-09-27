import { BEHAVIOR_LABELS, type Behavior } from "@/components/art/BehaviorFly";
import { ApiError } from "./client";

/** Keep only behaviours supported by the animation; preserve the server probabilities. */
export function behaviorProbabilities(data: Record<string, number>): Partial<Record<Behavior, number>> {
  const result: Partial<Record<Behavior, number>> = {};
  for (const behavior of Object.keys(BEHAVIOR_LABELS) as Behavior[]) {
    const probability = data[behavior];
    if (probability === undefined) continue;
    if (!Number.isFinite(probability) || probability < 0 || probability > 1) {
      throw new ApiError(502, "invalid_response", "行動の確率を読み取れませんでした。");
    }
    result[behavior] = probability;
  }
  if (!Object.values(result).some(probability => probability > 0)) {
    throw new ApiError(502, "invalid_response", "行動の観察記録がまだありません。");
  }
  return result;
}
