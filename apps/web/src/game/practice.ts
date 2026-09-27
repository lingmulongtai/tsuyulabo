/**
 * Local puzzle generators for practice / offline demo. Real play always uses the params issued by the
 * server (POST /v1/puzzles); these only mimic their shape so the screens can be tried without the API.
 */
import type { CleaningParams, Cue, Ingredient, MealParams, Shape, TemperatureParams, TrainingParams, Valence } from "./puzzles/types";

const SHAPE_WEIGHTS: Array<[Shape, number]> = [
  ["m1", 4], ["d2h", 4], ["d2v", 4], ["i3h", 3], ["i3v", 3],
  ["l3a", 3], ["l3b", 3], ["l3c", 3], ["l3d", 3], ["o4", 3],
  ["i4h", 2], ["i4v", 2], ["t4", 2], ["l4", 2], ["s4", 2],
  ["i5h", 1], ["i5v", 1], ["o9", 1],
];
const INGREDIENTS: Ingredient[] = ["banana", "apple", "grape", "yeast", "agar"];

/** Small deterministic PRNG (mulberry32) so a practice seed always gives the same puzzle. */
export function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function weighted<T>(rand: () => number, items: Array<[T, number]>): T {
  const total = items.reduce((s, [, w]) => s + w, 0);
  let x = rand() * total;
  for (const [item, w] of items) {
    x -= w;
    if (x < 0) return item;
  }
  return items[items.length - 1][0];
}

export function practiceMeal(seed = Date.now(), theme: Ingredient = "banana"): MealParams {
  const rand = rng(seed);
  const others = INGREDIENTS.filter((i) => i !== theme);
  const ingredientWeights: Array<[Ingredient, number]> = [[theme, 30], ...others.map((o) => [o, 17.5] as [Ingredient, number])];
  return {
    rows: 8,
    cols: 8,
    time_limit_ms: 30000,
    hand_size: 3,
    theme,
    pieces: Array.from({ length: 90 }, () => ({ shape: weighted(rand, SHAPE_WEIGHTS), ingredient: weighted(rand, ingredientWeights) })),
  };
}

/** The three demo boards from the planning document (5×5). */
const DEMO_TRAINING: Array<{ cue: Cue; valence: Valence; cp: Record<string, number> }> = [
  { cue: "banana", valence: "reward", cp: { "0,0": 1, "1,3": 2, "4,1": 3, "3,4": 4, "4,2": 5 } },
  { cue: "blue_light", valence: "reward", cp: { "2,2": 1, "2,3": 2, "0,0": 3, "4,4": 4, "4,0": 5 } },
  { cue: "apple_vinegar", valence: "punish", cp: { "0,4": 1, "4,4": 2, "0,0": 3, "4,0": 4, "4,2": 5 } },
];

export function practiceTraining(index = 0, cue?: Cue, valence?: Valence): TrainingParams {
  const demo = DEMO_TRAINING[index % DEMO_TRAINING.length];
  const n = 5;
  const checkpoints = Object.entries(demo.cp)
    .map(([rc, k]) => {
      const [r, c] = rc.split(",").map(Number);
      return { cell: r * n + c, k };
    })
    .sort((a, b) => a.k - b.k);
  return { n, checkpoints, cue: cue ?? demo.cue, valence: valence ?? demo.valence };
}

export function practiceCleaning(seed = Date.now()): CleaningParams {
  return { period_ms: 1400, taps: 3, zone: { center: 0.5, perfect: 0.06, good: 0.15 }, phase: rng(seed)() };
}

export function practiceTemperature(seed = Date.now()): TemperatureParams {
  return { period_ms: 1600, center_c: 25, amp_c: 7, phase: rng(seed)() };
}
