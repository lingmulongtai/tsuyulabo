import { expect, type Page } from "@playwright/test";
import { createMealGame, currentHand, place } from "../../src/game/puzzles/meal";
import { puzzleParams } from "../../src/lib/api/puzzle";
import type { PuzzleKind } from "../../src/game/puzzles/types";
import { apiAction, returnHome, type Schemas } from "./session";
import { solveTraining } from "./training-solver";
import { cleaningTimes, hintedSite, nextMealMove, temperatureTime } from "./capture-solvers";
import { MediaCapture } from "./capture-media";

async function open(page: Page, kind: PuzzleKind) {
  await page.locator(`a[href="/care/${kind === "pupation_site" ? "pupation" : kind}"]`).click();
}

async function puzzle(page: Page, kind: PuzzleKind) {
  if (kind === "training") {
    await open(page, kind);
    return apiAction<Schemas["Puzzle"]>(page, "/v1/puzzles", "POST", () =>
      page.getByRole("button", { name: /パズルをはじめる/ }).click());
  }
  return apiAction<Schemas["Puzzle"]>(page, "/v1/puzzles", "POST", () => open(page, kind));
}

async function submit(page: Page, issued: Schemas["Puzzle"], action: () => Promise<unknown>) {
  const result = await apiAction<Schemas["PuzzleResult"]>(page,
    `/v1/puzzles/${issued.puzzle_id}/submit`, "POST", action);
  expect(result.valid).not.toBe(false);
  return result;
}

export async function captureMeal(page: Page, media: MediaCapture, photograph = false) {
  const issued = await puzzle(page, "meal");
  const params = puzzleParams("meal", issued.params);
  let state = createMealGame(params);
  // Solve before starting the real 30-second clock.
  const plan = [];
  for (let i = 0; i < 48; i++) {
    const next = nextMealMove(state);
    if (!next) break;
    const result = place(state, next.p, next.r, next.c, 0);
    plan.push({ ...next, index: currentHand(state).indexOf(next.p), clears: result.state.lines > state.lines });
    state = result.state;
  }
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  await expect(page.getByRole("button", { name: /のブロック$/ }).first()).toBeEnabled();
  const started = Date.now();
  let moves = 0;
  for (const move of plan) {
    // Leave delivery grace and time for the result sheet.
    if (Date.now() - started > 25_000) break;
    await page.getByRole("button", { name: /のブロック$/ }).nth(move.index).click();
    await page.getByRole("button", { name: `${move.r + 1}行${move.c + 1}列`, exact: true }).click();
    moves++;
    if (photograph && move.clears) await media.shot(page, "meal");
  }
  const feed = page.getByRole("button", { name: "ツユにあげる", exact: true });
  await expect(feed).toBeVisible({ timeout: 40_000 });
  const result = await submit(page, issued, () => feed.click());
  expect(result.lines).toBeGreaterThan(0);
  expect(result.score).toBeGreaterThan(100);
  console.log(`meal: ${moves} moves, ${result.lines} lines, ${result.score} points`);
  await returnHome(page);
  return result;
}

export async function captureTraining(page: Page, media: MediaCapture, photograph = false) {
  const issued = await puzzle(page, "training");
  const params = puzzleParams("training", issued.params);
  const path = solveTraining(params);
  const circuit = page.getByRole("application", { name: "回路パズル" });
  await circuit.scrollIntoViewIfNeeded();
  const bounds = (await circuit.boundingBox())!;
  const point = (cell: number) => ({
    x: bounds.x + ((cell % params.n) + 0.5) * bounds.width / params.n,
    y: bounds.y + (Math.floor(cell / params.n) + 0.5) * bounds.height / params.n,
  });
  await page.mouse.move(point(path[0]).x, point(path[0]).y);
  await page.mouse.down();
  for (let i = 1; i < path.length; i++) {
    const next = point(path[i]);
    await page.mouse.move(next.x, next.y, { steps: 2 });
    if (photograph && i === Math.floor(path.length * 0.65)) {
      await media.shot(page, "training", { top: false });
    }
  }
  await page.mouse.up();
  await expect(page.getByText("PERFECT", { exact: true })).toBeVisible();
  if (photograph) {
    await page.waitForTimeout(1400); // Let all three stars appear.
    await media.shot(page, "training-result");
  }
  const result = await submit(page, issued, () => page.getByRole("button", { name: "ツユに教える", exact: true }).click());
  expect(result.stars).toBe(3);
  await returnHome(page);
}

export async function captureTiming(page: Page, kind: "cleaning" | "temperature", media: MediaCapture, photograph = false) {
  const issued = await puzzle(page, kind);
  const times = kind === "cleaning" ? cleaningTimes(puzzleParams(kind, issued.params)) :
    [temperatureTime(puzzleParams(kind, issued.params))];
  // Virtual clock makes pointer timing repeatable; real wall time still satisfies API anti-cheat.
  const wallStart = Date.now();
  await page.clock.pauseAt(await page.evaluate(() => Date.now() + 100));
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  let previous = 0;
  for (let i = 0; i < times.length; i++) {
    await page.clock.runFor(times[i] - previous);
    previous = times[i];
    if (photograph && (kind === "temperature" || i === 1)) await media.shot(page, kind, { paused: true });
    const tap = () => page.getByRole("button", { name: kind === "cleaning" ? `トン！ あと${times.length - i}回` : "ここでストップ！", exact: true }).click();
    if (i === times.length - 1) {
      const remaining = times[i] - (Date.now() - wallStart);
      if (remaining > 0) await new Promise(resolve => setTimeout(resolve, remaining));
      const result = await submit(page, issued, tap);
      expect(result.score).toBe(100);
      if (kind === "cleaning") expect(result.grades).toEqual(["perfect", "perfect", "perfect"]);
      else expect(result.grade).toBe("perfect");
    } else await tap();
  }
  await page.clock.resume();
  await returnHome(page);
}

export async function captureSite(page: Page) {
  const issued = await puzzle(page, "pupation_site");
  const option = hintedSite(puzzleParams("pupation_site", issued.params));
  const result = await submit(page, issued, () => page.getByRole("button")
    .filter({ hasText: option.label }).filter({ hasText: option.detail }).click());
  await returnHome(page);
  return result.hit;
}
