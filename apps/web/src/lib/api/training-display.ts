import type { Cue, Stars, Valence } from "@/game/puzzles/types";
import { CUE_INFO } from "@/game/labels";
import { ApiError } from "./client";

export interface TrainingOutcome {
  stars: Stars;
  hirameki: boolean;
  association: { cue: Cue; valence: Valence; value: number } | null;
  skillUnlocked: string | null;
}

/** Training fields are not yet included in the generated generic puzzle response. */
export function trainingOutcome(value: unknown): TrainingOutcome {
  const invalid = () => new ApiError(502, "invalid_response", "しつけの結果を読み取れませんでした。");
  if (!value || typeof value !== "object") throw invalid();
  const result = value as Record<string, unknown>;
  if ((result.stars !== 1 && result.stars !== 2 && result.stars !== 3) || typeof result.hirameki !== "boolean") throw invalid();
  let association: TrainingOutcome["association"] = null;
  if (result.association !== null) {
    if (!result.association || typeof result.association !== "object") throw invalid();
    const a = result.association as Record<string, unknown>;
    if (typeof a.cue !== "string" || !Object.hasOwn(CUE_INFO, a.cue) ||
      (a.valence !== "reward" && a.valence !== "punish") || typeof a.value !== "number" ||
      !Number.isFinite(a.value) || a.value < -1 || a.value > 1) throw invalid();
    association = { cue: a.cue as Cue, valence: a.valence, value: a.value };
  }
  if (result.skill_unlocked != null && typeof result.skill_unlocked !== "string") throw invalid();
  return { stars: result.stars, hirameki: result.hirameki, association, skillUnlocked: (result.skill_unlocked as string | null) ?? null };
}

export function canPracticeOffline(error: unknown) {
  return error instanceof ApiError && error.retryable && error.code !== "invalid_response";
}
