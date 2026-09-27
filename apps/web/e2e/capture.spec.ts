import { expect, test } from "@playwright/test";
import { copyFile } from "node:fs/promises";
import path from "node:path";
import { captureMeal, captureSite, captureTiming, captureTraining } from "./helpers/capture-care";
import { MediaCapture, rawRoot } from "./helpers/capture-media";
import { advanceTime, apiAction, openGuestHome, receiveEgg, type Schemas } from "./helpers/session";

test("capture a well cared-for week and the research notebook @capture", async ({ page }, testInfo) => {
  const media = new MediaCapture();
  await media.prepare(page);
  await openGuestHome(page);
  await advanceTime(page, "next_day");
  await receiveEgg(page);
  let siteHit: boolean | undefined;

  for (let day = 1; day <= 7; day++) {
    await test.step(`day ${day}: meals, care and learning`, async () => {
      if (day > 1) await advanceTime(page, "next_day");
      if (day === 1 || day === 6) await captureTiming(page, "temperature", media, day === 1);
      if (day >= 2 && day <= 5) await captureTiming(page, "cleaning", media, day === 3);
      for (let slot = 0; slot < 3; slot++) {
        if (slot > 0) await advanceTime(page, "next_slot");
        await captureMeal(page, media, day === 3 && slot === 0);
        if (day === 3 && slot === 0) {
          await expect(page.getByRole("heading", { level: 1 })).toContainText("研究3日目");
          await media.shot(page, "home");
        }
        if (day >= 2) await captureTraining(page, media, day === 3 && slot === 0);
        if (day === 5 && slot === 2) siteHit = await captureSite(page);
      }
    });
  }

  const presentation = await apiAction<Schemas["Presentation"]>(page,
    "/v1/weeks/current/presentation", "GET", () => page.getByRole("link", { name: /研究発表会へ/ }).click());
  expect(["gold", "rainbow"]).toContain(presentation.rank);
  expect(presentation.care_points).toBeGreaterThanOrEqual(3000);
  await expect(page.getByRole("button", { name: "羽化を見る", exact: true })).toBeVisible();
  await page.waitForTimeout(1000);
  await media.shot(page, "presentation");
  await page.getByRole("button", { name: "羽化を見る", exact: true }).click();
  const eclosion = await apiAction<Schemas["Eclosion"]>(page,
    "/v1/weeks/current/eclose", "POST", () => page.getByRole("button", { name: "羽化させる", exact: true }).click());
  await expect(page.getByRole("button", { name: "飼育室へ", exact: true })).toBeVisible();
  await page.waitForTimeout(1800);
  await media.shot(page, "eclosion");
  await page.getByRole("button", { name: "飼育室へ", exact: true }).click();
  await expect(page.getByText("脳のモデルが選んだ行動", { exact: false })).toBeVisible();
  await page.waitForTimeout(4500);
  await media.shot(page, "adult");

  await page.getByRole("link", { name: "この子の脳をのぞく →" }).click();
  await expect(page.getByLabel("何をしてみる？")).toHaveValue("sugar");
  await page.getByRole("button", { name: "再生", exact: true }).click();
  await page.waitForTimeout(1750);
  await expect(page.getByRole("button", { name: "一時停止", exact: true })).toBeVisible();
  await media.shot(page, "brain");

  await page.goto("/team");
  await page.getByRole("button", { name: "チームに選ぶ", exact: true }).click();
  await apiAction(page, "/v1/team", "PUT", () => page.getByRole("button", { name: "このチームにする（1/5）", exact: true }).click());
  await page.goto("/");
  await advanceTime(page, "next_slot");
  await page.goto("/team");
  await expect(page.getByRole("button", { name: /袋をあける（[1-9]/ })).toBeEnabled();
  await media.shot(page, "team");
  await page.goto("/zukan");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByText("行動の記録", { exact: true })).toBeVisible();
  await media.shot(page, "zukan");
  await page.goto("/daily");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.waitForTimeout(1500);
  await media.shot(page, "daily");

  await page.goto("/race");
  await expect(page.getByText("走るツユを選ぶ", { exact: false })).toBeVisible();
  // The maze changes every week, so pick open cells from the board instead of fixed coordinates.
  const openCells = page.getByRole("button", { name: /^\d+列\d+行$/ });
  const cellCount = await openCells.count();
  for (const index of [Math.floor(cellCount * 0.55), Math.floor(cellCount * 0.8)]) await openCells.nth(index).click();
  await page.getByRole("button", { name: "この作戦で走る", exact: true }).click();
  const replay = page.getByRole("heading", { name: /走りを振り返る/ });
  await expect(replay).toBeVisible({ timeout: 60_000 });
  await page.getByRole("button", { name: "再生", exact: true }).click();
  await page.waitForTimeout(2500);
  await replay.scrollIntoViewIfNeeded();
  await media.shot(page, "race", { top: false });

  await page.goto("/shiori");
  await page.getByLabel("気になること").fill("しつけをすると、ツユの脳はどう変わるの？");
  await page.getByRole("button", { name: "シオリに聞く", exact: true }).click();
  // The heading also contains the AI badge, so match the start of the text.
  const answer = page.getByText(/^シオリからの答え/).first();
  await expect(answer).toBeVisible({ timeout: 90_000 });
  await answer.scrollIntoViewIfNeeded();
  await media.shot(page, "shiori", { top: false });

  await media.finish({ presentation, pupationHit: siteHit, adultStars: eclosion.adult.stars });
  await testInfo.attach("care-results", { body: JSON.stringify({ presentation, pupationHit: siteHit }), contentType: "application/json" });
  // Closing the page finalizes the recording before the optional encoder starts.
  const video = page.video();
  await page.close();
  if (video) await copyFile(await video.path(), path.join(rawRoot, "playthrough-raw.webm"));
});
