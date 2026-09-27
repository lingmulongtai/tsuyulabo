/** Innate traits (docs/specs/game-rules.md §7). They come from the brain model's individual parameters. */
export const TRAIT_INFO: Record<string, { name: string; note: string }> = {
  right_turner: { name: "右曲がりぐせ", note: "左右の旋回ニューロンのつながりが少し右寄り" },
  left_turner: { name: "左曲がりぐせ", note: "左右の旋回ニューロンのつながりが少し左寄り" },
  light_lover: { name: "光が大好き", note: "光を見ると前に進みやすい" },
  keen_nose: { name: "匂いにするどい", note: "匂いの受容体の感度が高い" },
  brave: { name: "度胸がある", note: "迫る影でも逃げ出しにくい" },
  wanderer: { name: "よく歩く", note: "歩行ニューロンが自分から発火しやすい" },
  easygoing: { name: "のんびりや", note: "歩行ニューロンが静か" },
  glutton: { name: "食いしんぼう", note: "糖の味で口吻が伸びやすい" },
};

export function traitName(id: string) {
  return TRAIT_INFO[id]?.name ?? id;
}

export const TIER_NAMES = ["ノーマル", "グッド", "スーパー", "突然変異！"] as const;
export const TIER_COLORS = ["#FFFFFF", "#7FC8FF", "#FFD54A", "rainbow"] as const;
export const RANK_LABELS = { normal: "ノーマル", silver: "シルバー", gold: "ゴールド", rainbow: "にじ" } as const;
