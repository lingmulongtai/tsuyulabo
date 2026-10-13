import { expect, type Locator, type Page } from "@playwright/test";
import { SHAPES } from "../../src/game/puzzles/meal";
import { puzzleParams } from "../../src/lib/api/puzzle";
import type { PuzzleKind } from "../../src/game/puzzles/types";
import { apiAction, openCareSheet, returnHome, type Schemas } from "./session";
import { solveTraining } from "./training-solver";
import { captureVial } from "./vial-media";

async function openPuzzle(page: Page, kind: PuzzleKind) {
  await openCareSheet(page);
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
  await page.getByRole("slider", { name: "湿度ダイヤル" }).focus();
  await page.getByRole("slider", { name: "湿度ダイヤル" }).press("ArrowRight");
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  const result = await submit(page, puzzle, () =>
    page.getByRole("button", { name: "ここでストップ！", exact: true }).click());
  // Timing and random phase affect the score; acceptance of real input is the contract.
  expect(result.score).toBeGreaterThanOrEqual(0);
  expect(result.score).toBeLessThanOrEqual(100);
  expect(result.vial?.humidity).toBeGreaterThanOrEqual(0.2);
  await expect(page.getByText("お世話できました！", { exact: true })).toBeVisible();
  await returnHome(page);
}

export async function playCleaning(page: Page, capture = false) {
  const puzzle = await openPuzzle(page, "cleaning");
  const surface = page.locator("[data-care-vial]");
  await expect(surface.locator("canvas[data-ready='true']")).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  await surface.scrollIntoViewIfNeeded();
  const bounds = await box(surface);
  await page.mouse.move(bounds.x + bounds.width * 0.46, bounds.y + bounds.height * 0.4);
  await page.mouse.down();
  for (let i = 0; i < 6; i++) await page.mouse.move(bounds.x + bounds.width * (0.46 + i * 0.02), bounds.y + bounds.height * (0.4 + i * 0.03), { steps: 2 });
  await page.mouse.up();
  await expect(page.getByRole("button", { name: "拭き終わる", exact: true })).toBeEnabled();
  if (capture) await captureVial(page, "cleaning", "[data-care-vial]");
  const result = await submit(page, puzzle, () =>
    page.getByRole("button", { name: "拭き終わる", exact: true }).click());
  expect(result.grades).toHaveLength(3);
  expect(result.score).toBeGreaterThanOrEqual(15);
  expect(result.vial?.grime).toBeLessThanOrEqual(1);
  await returnHome(page);
}

export async function playMeal(page: Page, capture = false) {
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
  const ghost = await box(page.locator("[data-meal-drag]"));
  expect(ghost.x).toBeCloseTo(board.x, 0);
  expect(ghost.y).toBeCloseTo(board.y, 0);
  await page.mouse.up();
  await expect(page.getByRole("button", { name: /のブロック$/ })).toHaveCount(params.hand_size - 1);
  const feed = page.getByRole("button", { name: "ツユにあげる", exact: true });
  await expect(feed).toBeVisible({ timeout: params.time_limit_ms + 10_000 });
  const result = await submit(page, puzzle, () => feed.click());
  expect(result.score).toBe(shape.length);
  expect(result.effects?.hunger).toBeGreaterThan(0);
  expect(result.vial?.food.nutrition).toBeGreaterThan(0);
  if (capture) await captureVial(page, "meal-vial", "[data-care-vial]");
  await returnHome(page);
  return result;
}

export async function playTraining(page: Page, expectedSize: number) {
  const puzzle = await openPuzzle(page, "training");
  // The development-only clock floats over lower board cells on a phone.
  await page.getByRole("complementary", { name: "開発用の時間操作" }).evaluate(element => { element.style.pointerEvents = "none"; });
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
  await expect(page.getByText(`1/${params.n * params.n}`, { exact: true })).toBeVisible();
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
  const observe = page.getByRole("button", { name: /を置く$/, exact: false });
  await expect(observe).toBeEnabled();
  await observe.click();
  await expect(page.getByRole("status").filter({ hasText: /寄っていった|離れていった|じっとしていた/ })).toBeVisible({ timeout: 30_000 });
  await returnHome(page);
}

export async function choosePupationSite(page: Page) {
  const puzzle = await openPuzzle(page, "pupation_site");
  const params = puzzleParams("pupation_site", puzzle.params);
  const surface = page.locator("[data-care-vial]");
  await expect(surface.locator("canvas[data-ready='true']")).toBeVisible({ timeout: 30_000 });
  await surface.scrollIntoViewIfNeeded();
  const bounds = await box(surface);
  await page.mouse.click(bounds.x + bounds.width * 0.5, bounds.y + bounds.height * 0.25);
  const selected = page.locator("button[aria-pressed='true']");
  await expect(selected).toHaveCount(1);
  const label = await selected.innerText();
  const option = params.options.find(value => label.includes(value.label) && label.includes(value.detail));
  expect(option).toBeDefined();
  const result = await submit(page, puzzle, () => page.getByRole("button", { name: "この場所で見守る", exact: true }).click());
  expect(typeof result.hit).toBe("boolean"); // The correct answer is deliberately server-only.
  expect(result.vial?.pupation_position).toEqual(option!.position);
  await returnHome(page);
}
