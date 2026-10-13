import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";
import { advanceTime, apiAction, openGuestHome, receiveEgg, type Schemas } from "./helpers/session";

const media = process.env.W19_MEDIA_DIR ?? path.resolve(__dirname, "../../../docs/media/v2/w19");
async function capture(page: Page, name: string) {
  await mkdir(media, { recursive: true });
  await sharp(await page.screenshot({ style: 'aside[aria-label="開発用の時間操作"] { visibility: hidden !important; }' })).webp({ quality: 90 }).toFile(path.join(media, `${name}.webp`));
}
async function pauseScene(page: Page) {
  const pause = page.getByRole("button", { name: "動きを一時停止", exact: true });
  if (await pause.count()) await pause.click();
  await expect(page.locator("[data-home-vial] canvas[data-ready='true']")).toBeVisible({ timeout: 60_000 });
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
}

test("phone scenes stay full bleed with an accessible care sheet and cached individual portraits", async ({ page }) => {
  test.setTimeout(300_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" });
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await openGuestHome(page);
  await advanceTime(page, "next_day");
  await receiveEgg(page);
  await pauseScene(page);
  const bounds = await page.locator("[data-home-vial]").boundingBox();
  expect(bounds).toMatchObject({ x: 0, y: 0, width: 390, height: 844 });
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).colorScheme)).toBe("dark");
  const sheet = page.locator("[data-care-sheet]");
  expect((await sheet.boundingBox())!.height).toBeLessThan(844 * .27);
  await expect(sheet.locator('a[href^="/care/"]')).toHaveCount(2);
  expect(await sheet.evaluate(element => getComputedStyle(element).animationName)).toBe("none");
  await capture(page, "home-egg");

  const handle = sheet.getByRole("button", { name: "今日のお世話をすべて見る", exact: true });
  await handle.focus(); await handle.press("ArrowUp");
  await expect(sheet).toHaveAttribute("data-expanded", "true");
  await expect(sheet.getByText("きょうのやること", { exact: true })).toBeVisible();
  await capture(page, "care-list");
  await sheet.getByRole("button", { name: "今日のお世話を閉じる", exact: true }).press("Escape");
  await expect(sheet).toHaveAttribute("data-expanded", "false");
  const grip = (await handle.boundingBox())!;
  await page.mouse.move(grip.x + grip.width / 2, grip.y + 18); await page.mouse.down();
  await page.mouse.move(grip.x + grip.width / 2, grip.y - 80, { steps: 5 }); await page.mouse.up();
  await expect(sheet).toHaveAttribute("data-expanded", "true");

  await page.locator('a[href="/care/meal"]').click();
  await expect(page.getByRole("heading", { name: "ごはんづくり", exact: true })).toBeVisible();
  await expect(page.locator('canvas[data-ready="true"]')).toHaveCount(1);
  await expect(page.getByRole("button", { name: "スタート", exact: true })).toBeEnabled();
  const puzzleSheet = page.getByRole("region", { name: "ごはんづくり", exact: true });
  const sheetTop = (await puzzleSheet.boundingBox())!.y;
  expect(sheetTop).toBeGreaterThan(844 * .4);
  await puzzleSheet.evaluate(element => { element.scrollTop = element.scrollHeight; });
  expect((await puzzleSheet.boundingBox())!.y).toBeCloseTo(sheetTop, 1);
  expect(await page.evaluate(() => scrollY)).toBe(0);
  await puzzleSheet.evaluate(element => { element.scrollTop = 0; });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await expect.poll(() => puzzleSheet.evaluate(element => getComputedStyle(element).transform)).toBe("none");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await capture(page, "care-meal");
  await page.getByRole("link", { name: "ホームへもどる", exact: true }).click();
  for (const stage of ["larva1", "larva2", "larva3", "wandering", "pupa"]) {
    const home = await advanceTime(page, "next_day");
    expect(home.fly?.stage).toBe(stage);
    await pauseScene(page); await capture(page, `home-${stage}`);
  }
  await advanceTime(page, "eclosion");
  await page.getByRole("link", { name: /羽化の日へ/ }).click();
  await page.getByRole("button", { name: "羽化を見る", exact: true }).click();
  const eclosed = await apiAction<Schemas["Eclosion"]>(page, "/v1/weeks/current/eclose", "POST", () => page.getByRole("button", { name: "羽化を見届ける", exact: true }).click());
  await page.getByRole("button", { name: "スキップ", exact: true }).click();
  await page.getByRole("button", { name: "飼育室へ", exact: true }).click();
  await page.getByRole("link", { name: "お世話", exact: true }).click();
  await pauseScene(page); await capture(page, "home-adult");
  await page.getByRole("link", { name: "おやすみ", exact: true }).click();
  await expect(page.getByRole("heading", { name: "ツユとひとやすみ", exact: true })).toBeVisible();
  await expect(page.locator("[data-care-stage]")).toHaveAttribute("data-care-stage", "adult");
  await expect(page.locator("canvas[data-ready='true']")).toBeVisible();
  await capture(page, "care-sleep");
  await page.getByRole("link", { name: "ホームへもどる", exact: true }).click();

  await page.getByRole("link", { name: "コロニー", exact: true }).click();
  await page.getByRole("button", { name: "コロニーに選ぶ", exact: true }).click();
  await apiAction<Schemas["Team"]>(page, "/v1/team", "PUT", () => page.getByRole("button", { name: /このコロニーにする/ }).click());
  await page.reload(); // Cold gallery load must wait for Scene rather than cache its loading preview.
  await expect(page.locator('[data-portrait-ready="true"] img').first()).toBeVisible({ timeout: 60_000 });
  await expect(page.locator('[data-portrait-ready="true"] img').first()).toHaveAttribute("src", /^data:image\/webp/);
  await expect(page.getByRole("heading", { name: eclosed.adult.name, exact: true }).first()).toBeVisible();
  await capture(page, "colony");
  await page.getByRole("link", { name: "図鑑", exact: true }).click();
  await expect(page.locator('[data-portrait-ready="true"] img').first()).toBeVisible();
  await page.waitForFunction(() => [...document.querySelectorAll<HTMLElement>("[data-portrait]")].every(element => {
    const rect = element.getBoundingClientRect();
    return rect.top >= innerHeight || rect.bottom <= 0 || element.dataset.portraitReady === "true" || Boolean(element.querySelector('[aria-label="まだ出会っていません"]'));
  }));
  await capture(page, "collection");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
