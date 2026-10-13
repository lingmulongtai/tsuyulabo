import { expect, it } from "vitest";
import { wipePreview } from "./wiping";
it("matches server coverage thresholds and rewards", () => {
  const strokes = Array.from({ length: 54 }, (_, i) => ({ u: (i % 6 + 0.5) / 6, v: (Math.floor(i / 6) + 0.5) / 9, t: i * 40 }));
  expect(wipePreview(strokes, 2200)).toMatchObject({ score: 100, coverage: 1 });
  expect(wipePreview(strokes, 8000).score).toBe(66);
  expect(wipePreview(strokes.slice(0, 2), 100).score).toBe(15);
});
