import type { TierIndex } from "@/game/expectation";
import type { Strain } from "../art/palette";
import type { EclosionResult } from "./EclosionStage";

/** Public odds table (docs/specs/game-rules.md §7), used by the demo and the odds display. */
export const ODDS: Record<"normal" | "silver" | "gold" | "rainbow", [number, number, number, number]> = {
  normal: [72, 22, 5.5, 0.5],
  silver: [60, 30, 9, 1],
  gold: [40, 38, 18, 4],
  rainbow: [20, 40, 30, 10],
};

const MUTANTS: Strain[] = ["white", "yellow", "ebony", "curly", "vestigial"];
const TRAITS = ["right_turner", "left_turner", "light_lover", "keen_nose", "brave", "wanderer", "easygoing", "glutton"];
const EXCLUSIVE: Array<[string, string]> = [
  ["right_turner", "left_turner"],
  ["wanderer", "easygoing"],
];
const NAMES = ["ぴかり", "こむぎ", "しずく", "あめ", "つゆまる", "ルビー", "もなか", "すだち"];

const pick = <T,>(a: T[]) => a[Math.floor(Math.random() * a.length)];

/** Client-side roll for the demo only — real eclosion is decided by the server. */
export function demoEclosion(rank: keyof typeof ODDS): EclosionResult {
  const odds = ODDS[rank];
  let x = Math.random() * 100;
  let tier: TierIndex = 0;
  for (let i = 0; i < 4; i++) {
    x -= odds[i];
    if (x < 0) {
      tier = i as TierIndex;
      break;
    }
  }
  const seq = Array.from({ length: tier + 1 }, (_, i) => i);
  if (tier === 2 && Math.random() < 0.3) seq.push(3, 2); // occasional fake-out: flashes rainbow, falls back

  const traits: string[] = [];
  while (traits.length < 2) {
    const t = pick(TRAITS);
    if (traits.includes(t)) continue;
    if (EXCLUSIVE.some(([a, b]) => (t === a && traits.includes(b)) || (t === b && traits.includes(a)))) continue;
    traits.push(t);
  }
  return {
    tier,
    omen_sequence: seq,
    adult: {
      name: pick(NAMES),
      strain: tier === 3 ? pick(MUTANTS) : "wild",
      sex: Math.random() < 0.5 ? "m" : "f",
      stars: tier === 0 ? (Math.random() < 0.5 ? 1 : 2) : tier + 2,
      traits,
    },
  };
}
