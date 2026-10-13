import type { Grade } from "./types";
export interface WipeStamp { u: number; v: number; t: number }
export interface WipeSubmission { strokes: readonly WipeStamp[]; elapsed_ms: number }
export function wipeMask(strokes: readonly Pick<WipeStamp, "u" | "v">[]): boolean[] {
  const mask = Array<boolean>(18 * 12).fill(false);
  for (const { u, v } of strokes) for (let row = 0; row < 18; row++) for (let col = 0; col < 12; col++) {
    if (Math.hypot((col + 0.5) / 12 - u, (row + 0.5) / 18 - v) <= 0.12) mask[row * 12 + col] = true;
  }
  return mask;
}
/** Preview only; the API verifies stamps and elapsed time before awarding anything. */
export function wipePreview(strokes: readonly WipeStamp[], elapsed: number) {
  const mask = wipeMask(strokes);
  const grades: Grade[] = Array.from({ length: 3 }, (_, zone) => {
    const coverage = mask.slice(zone * 72, (zone + 1) * 72).filter(Boolean).length / 72;
    return coverage >= 0.75 && elapsed <= 7000 ? "perfect" : coverage >= 0.45 ? "good" : "miss";
  });
  const points = { perfect: 34, good: 22, miss: 5 };
  return { coverage: mask.filter(Boolean).length / mask.length, grades, score: Math.min(100, grades.reduce((sum, g) => sum + points[g], 0)) };
}
