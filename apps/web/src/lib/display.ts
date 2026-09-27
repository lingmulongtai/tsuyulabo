import type { components } from "./api/schema";

export const MATERIAL_LABELS: Record<string, string> = { banana: "バナナ", apple: "りんご", grape: "ぶどう", yeast: "酵母", agar: "寒天", royal_jelly: "ローヤルゼリー" };
export const TRAIT_LABELS: Record<string, string> = { right_turner: "右曲がりぐせ", left_turner: "左曲がりぐせ", light_lover: "光が大好き", keen_nose: "匂いにするどい", brave: "度胸がある", wanderer: "よく歩く", easygoing: "のんびりや", glutton: "食いしんぼう" };
export const SUBSKILL_LABELS: Record<string, string> = { gather_s: "採集量アップS", gather_m: "採集量アップM", great_up: "大成功率アップ", drop_bonus: "しずくボーナス", bag_up: "材料袋アップ", energy_up: "げんき回復アップ", rp_up: "研究ポイントアップ" };
export const SKILL_LABELS: Record<string, string> = { banana_search: "バナナさがし", banana_avoid: "バナナよけ", apple_search: "りんごさがし", apple_avoid: "りんごよけ", yeast_search: "酵母さがし", yeast_avoid: "酵母よけ", grape_search: "ぶどうさがし", grape_avoid: "ぶどうよけ", light_search: "光さがし", light_avoid: "光よけ" };
export const BEHAVIOR_LABELS: Record<string, string> = { rest: "ひとやすみ", walk: "歩く", turn_left: "左に曲がる", turn_right: "右に曲がる", feed: "食べる", escape: "逃げる", groom: "毛づくろい", approach: "近づく", avoid: "離れる" };

export function preferencePercent(value: number) {
  return Math.round((Math.max(-1, Math.min(1, Number.isFinite(value) ? value : 0)) + 1) * 50);
}

export function bagCapacity(subskills: readonly string[]) {
  return 30 + subskills.filter(skill => skill === "bag_up").length * 10;
}

export function notificationText(notification: components["schemas"]["Notification"]) {
  const p = notification.payload;
  const name = typeof p.display_name === "string" ? p.display_name : "フレンド";
  if (notification.kind === "like") return `${name}さんが、いいねしてくれました。`;
  if (notification.kind === "gift") return `${name}さんから、${MATERIAL_LABELS[String(p.material)] ?? "材料"}を${typeof p.amount === "number" ? p.amount : "少し"}個おすそわけ。`;
  if (notification.kind === "eclosion") return `${name}さんの子が、${({ normal: "ノーマル", silver: "シルバー", gold: "ゴールド", rainbow: "にじ" } as Record<string, string>)[String(p.rank)] ?? "新しい"}ランクで羽化しました！`;
  return "研究所から新しいお知らせが届きました。";
}

export function shioriAnswer(result: Record<string, unknown> | null) {
  const evidence = result?.evidence;
  return {
    answer: typeof result?.answer === "string" ? result.answer : null,
    evidence: Array.isArray(evidence) ? evidence.filter((id): id is string => typeof id === "string") : [],
  };
}
