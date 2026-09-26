/** `rainbow` is a semantic color token: render it with a gradient in the UI. */
export const TIERS = [
  { id: "white", label: "白", color: "#FFFFFF" },
  { id: "blue", label: "青", color: "#7FC8FF" },
  { id: "gold", label: "金", color: "#FFD54A" },
  { id: "rainbow", label: "虹", color: "rainbow" },
] as const;

export type Tier = (typeof TIERS)[number];
export type TierIndex = 0 | 1 | 2 | 3;
export type WeekRank = "normal" | "silver" | "gold" | "rainbow";

/** Clamp animation counters; non-finite values fall back to white. */
export function tierForIndex(index: number): Tier {
  const safeIndex = Number.isFinite(index) ? Math.max(0, Math.min(3, Math.floor(index))) : 0;
  return TIERS[safeIndex];
}

const RANK_TIERS: Record<WeekRank, TierIndex> = { normal: 0, silver: 1, gold: 2, rainbow: 3 };

/** Rank display color, not a prediction of the server's random eclosion outcome. */
export function tierForRank(rank: WeekRank): Tier {
  return TIERS[RANK_TIERS[rank]];
}
