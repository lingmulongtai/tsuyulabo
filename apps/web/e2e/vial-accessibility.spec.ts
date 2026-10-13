import { expect, test } from "@playwright/test";
import { advanceTime, apiAction, openCareSheet, openGuestHome, receiveEgg, type Schemas } from "./helpers/session";

test("phone fallback supports glass wiping and a single swipeable colony surface", async ({ page }) => {
  test.setTimeout(process.env.E2E_SOFTWARE_WEBGL === "1" ? 240_000 : 120_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...args: unknown[]) {
      if (type.startsWith("webgl") || type === "experimental-webgl") return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await openGuestHome(page);
  await expect(page.locator("[data-home-vial]")).toHaveCount(0);
  await advanceTime(page, "next_day");
  const week = await receiveEgg(page);
  await expect(page.locator("[data-vivarium-fallback]")).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await advanceTime(page, "next_day");
  await openCareSheet(page);
  const puzzle = await apiAction<Schemas["Puzzle"]>(page, "/v1/puzzles", "POST", () => page.locator('a[href="/care/cleaning"]').click());
  await page.getByText("静止画・キーボードで拭く", { exact: true }).click();
  await page.getByRole("button", { name: "スタート", exact: true }).click();
  const pad = page.getByRole("group", { name: "ガラスの清掃面" });
  for (let row = 1; row <= 9; row++) for (let col = 1; col <= 6; col++) {
    const cell = pad.getByRole("button", { name: `ガラス ${row}行${col}列`, exact: true });
    await cell.press("Enter");
  }
  await expect(page.getByRole("status").filter({ hasText: /拭いたところ 100%/ })).toBeVisible();
  const cleaned = await apiAction<Schemas["PuzzleResult"]>(page, `/v1/puzzles/${puzzle.puzzle_id}/submit`, "POST", () => page.getByRole("button", { name: "拭き終わる", exact: true }).click());
  // Full coverage can still earn GOOD when real keyboard input takes over seven seconds.
  expect([66, 100]).toContain(cleaned.score);
  expect(cleaned.grades).toEqual(Array(3).fill(cleaned.score === 100 ? "perfect" : "good"));
  expect(cleaned.vial?.grime).toBeLessThan(0.2);
  await page.getByRole("link", { name: "ホームへ", exact: true }).click();
  await advanceTime(page, "eclosion");
  await page.getByRole("link", { name: /羽化の日へ/ }).click();
  await page.getByRole("button", { name: "羽化を見る", exact: true }).click();
  const adult = await apiAction<Schemas["Eclosion"]>(page, "/v1/weeks/current/eclose", "POST", () => page.getByRole("button", { name: "羽化を見届ける", exact: true }).click());
  await page.getByRole("button", { name: "スキップ", exact: true }).click();
  await page.getByRole("button", { name: "飼育室へ", exact: true }).click();
  await page.getByRole("link", { name: "お世話", exact: true }).click();
  await receiveEgg(page);
  const home = page.locator("[data-home-vial]");
  await home.getByRole("button", { name: "次のびん", exact: true }).click();
  await expect(home).toContainText(adult.adult.name);
  const strip = home.locator("div").filter({ has: page.getByRole("button", { name: "前のびん", exact: true }) }).last();
  const bounds = await strip.boundingBox();
  expect(bounds).not.toBeNull();
  const label = (await strip.locator("span").boundingBox())!;
  await page.mouse.move(label.x + label.width / 2, label.y + label.height / 2); await page.mouse.down();
  await page.mouse.move(label.x + label.width / 2 + 70, label.y + label.height / 2, { steps: 5 }); await page.mouse.up();
  await expect(home).toContainText("この子の一週間");
  await expect(home.locator("[data-vivarium-fallback]")).toHaveCount(1);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(week.id).toBeTruthy();
});
