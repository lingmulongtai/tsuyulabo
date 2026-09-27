import type { EclosionResult } from "@/components/eclosion/EclosionStage";
import type { WeekRank } from "@/game/expectation";
import { ApiError } from "./client";
import type { components } from "./schema";

export type EclosionOdds = Record<WeekRank, [number, number, number, number]>;

const isTier = (value: number): value is EclosionResult["tier"] => Number.isInteger(value) && value >= 0 && value <= 3;

export function eclosionResult(data: components["schemas"]["Eclosion"]): EclosionResult {
  if (!isTier(data.tier) || !data.omen_sequence.every(isTier)) {
    throw new ApiError(502, "invalid_response", "羽化の予兆を読み取れませんでした。");
  }
  const { name, strain, sex, stars, traits } = data.adult;
  return { tier: data.tier, omen_sequence: [...data.omen_sequence], adult: { name, strain, sex, stars, traits: [...traits] } };
}

/** Odds are percentages already; do not scale them as probabilities. */
export function eclosionOdds(value: unknown): EclosionOdds {
  const invalid = () => new ApiError(502, "invalid_response", "羽化の確率表を読み取れませんでした。");
  if (!value || typeof value !== "object" || !("eclosion" in value) || !value.eclosion || typeof value.eclosion !== "object") throw invalid();
  const source = value.eclosion as Record<string, unknown>;
  const result = {} as EclosionOdds;
  for (const rank of ["normal", "silver", "gold", "rainbow"] as const) {
    const row = source[rank];
    if (!Array.isArray(row) || row.length !== 4 || !row.every(p => typeof p === "number" && Number.isFinite(p) && p >= 0 && p <= 100)) throw invalid();
    result[rank] = [row[0], row[1], row[2], row[3]];
  }
  return result;
}
