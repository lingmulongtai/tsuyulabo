import { expect, type Locator, type Page } from "@playwright/test";
import { SHAPES } from "../../src/game/puzzles/meal";
import { puzzleParams } from "../../src/lib/api/puzzle";
import type { PuzzleKind } from "../../src/game/puzzles/types";
import { apiAction, returnHome, type Schemas } from "./session";
import { solveTraining } from "./training-solver";

async function openPuzzle(page: Page, kind: PuzzleKind) {
  const route = kind === "pupation_site" ? "pupation" : kind;
  const action = () => page.locator(`a[href="/care/${route}"]`).click();
  if (kind === "training") {
    await action();
    return apiAction<Schemas["Puzzle"]>(page, "/v1/puzzles", "POST", () =>
      page.getByRole("button", { name: /パズルをはじめる/ }).click());
  }
  const puzzle = await apiAction<Schemas["Puzzle"]>(page, "/v1/puzzles", "POST", action);
  expect(puzzle.kind).toBe(kind);
  return puzzle;
}

async function submit(page: Page, puzzle: Schemas["Puzzle"], action: () => Promise<unknown>) {
  const result = await apiAction<Schemas["PuzzleResult"]>(page,
    `/v1/puzzles/${puzzle.puzzle_id}/submit`, "POST", action);
  expect(result.valid).not.toBe(false);
  return result;
}

async function box(locator: Locator) {
  await expect(locator).toBeVisible();
  const bounds = await locator.boundingBox();
  expect(bounds).not.toBeNull();
  return bounds!;
}

export async function playTemperature(page: Page) {
  const puzzle = await openPuzzle(page, "temperature");
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  const result = await submit(page, puzzle, () =>
    page.getByRole("button", { name: "ここでストップ！", exact: true }).click());
  // Timing and random phase affect the score; acceptance of real input is the contract.
  expect(result.score).toBeGreaterThanOrEqual(0);
  expect(result.score).toBeLessThanOrEqual(100);
  await expect(page.getByText("お世話できました！", { exact: true })).toBeVisible();
  await returnHome(page);
}

export async function playCleaning(page: Page) {
  const puzzle = await openPuzzle(page, "cleaning");
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  // The large tap control stays still while the bottle itself shakes.
  await page.getByRole("button", { name: "トン！ あと3回", exact: true }).click();
  await page.getByRole("button", { name: "トン！ あと2回", exact: true }).click();
  const result = await submit(page, puzzle, () =>
    page.getByRole("button", { name: "トン！ あと1回", exact: true }).click());
  expect(result.grades).toHaveLength(3);
  expect(result.score).toBeGreaterThanOrEqual(15);
  await returnHome(page);
}

export async function playMeal(page: Page) {
  const puzzle = await openPuzzle(page, "meal");
  const params = puzzleParams("meal", puzzle.params);
  const shape = SHAPES[params.pieces[0].shape];
  const height = Math.max(...shape.map(([r]) => r)) + 1;
  const width = Math.max(...shape.map(([, c]) => c)) + 1;
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  const piece = page.getByRole("button", { name: /のブロック$/ }).first();
  await expect(piece).toBeEnabled(); // Includes the real countdown.
  await piece.scrollIntoViewIfNeeded();
  const source = await box(piece);
  // MealGame anchors the floating piece 56px above the pointer. Drop its top-left at (0,0).
  const board = await box(page.getByRole("button", { name: "1行1列", exact: true }).locator(".."));
  const cell = board.width / params.cols;
  await page.mouse.move(source.x + source.width / 2, source.y + source.height / 2);
  await page.mouse.down();
  await page.mouse.move(board.x + width * cell / 2, board.y + 56 + height * cell, { steps: 12 });
  await page.mouse.up();
  await expect(page.getByRole("button", { name: /のブロック$/ })).toHaveCount(params.hand_size - 1);
  const feed = page.getByRole("button", { name: "ツユにあげる", exact: true });
  await expect(feed).toBeVisible({ timeout: params.time_limit_ms + 10_000 });
  const result = await submit(page, puzzle, () => feed.click());
  expect(result.score).toBe(shape.length);
  expect(result.effects?.hunger).toBeGreaterThan(0);
  await returnHome(page);
}

export async function playTraining(page: Page, expectedSize: number) {
  const puzzle = await openPuzzle(page, "training");
  expect(puzzle.kind).toBe("training");
  const params = puzzleParams("training", puzzle.params);
  expect(params.n).toBe(expectedSize);
  const path = solveTraining(params);
  const circuit = page.getByRole("application", { name: "回路パズル" });
  await circuit.scrollIntoViewIfNeeded();
  const bounds = await box(circuit);
  const point = (cell: number) => ({
    x: bounds.x + ((cell % params.n) + 0.5) * bounds.width / params.n,
    y: bounds.y + (Math.floor(cell / params.n) + 0.5) * bounds.height / params.n,
  });
  const start = point(path[0]);
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  for (const cell of path.slice(1)) {
    const next = point(cell);
    await page.mouse.move(next.x, next.y, { steps: 2 });
  }
  await page.mouse.up();
  await expect(page.getByText("つながった！", { exact: true })).toBeVisible();
  const result = await submit(page, puzzle, () =>
    page.getByRole("button", { name: "ツユに教える", exact: true }).click());
  expect(result.stars).toBeGreaterThanOrEqual(1);
  expect(result.stars).toBeLessThanOrEqual(3);
  await expect(page.getByText("覚えた！", { exact: true })).toBeVisible();
  await returnHome(page);
}

export async function choosePupationSite(page: Page) {
  const puzzle = await openPuzzle(page, "pupation_site");
  const params = puzzleParams("pupation_site", puzzle.params);
  const option = params.options[0];
  const result = await submit(page, puzzle, () => page.getByRole("button")
    .filter({ hasText: option.label }).filter({ hasText: option.detail }).click());
  expect(typeof result.hit).toBe("boolean"); // The correct answer is deliberately server-only.
  await returnHome(page);
}
