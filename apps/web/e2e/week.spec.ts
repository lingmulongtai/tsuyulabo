import { expect, test } from "@playwright/test";
import { choosePupationSite, playCleaning, playMeal, playTemperature, playTraining } from "./helpers/care";
import { advanceTime, apiAction, openGuestHome, receiveEgg, type Schemas } from "./helpers/session";

test("a guest raises a fly through day seven and keeps the eclosed adult", async ({ page }) => {
  test.setTimeout(240_000);
  await openGuestHome(page);
  // Start at 04:00 JST regardless of when a developer/nightly run starts.
  await advanceTime(page, "next_day");
  const week = await receiveEgg(page);
  expect(week.fly.stage).toBe("egg");

  await test.step("day 1: temperature, bedding meal, and hatching at night", async () => {
    await playTemperature(page);
    await playMeal(page);
    const noon = await advanceTime(page, "next_slot");
    expect(noon.clock.slot).toBe("noon");
    expect(noon.fly?.stage).toBe("egg");
    const night = await advanceTime(page, "next_slot");
    expect(night.clock.slot).toBe("night");
    expect(night.fly?.stage).toBe("larva1");
  });

  const stages = ["larva1", "larva2", "larva3", "wandering", "pupa", "pupa"];
  for (let day = 2; day <= 7; day++) {
    await test.step(`day ${day}: ${stages[day - 2]}`, async () => {
      const home = await advanceTime(page, "next_day");
      expect(home.week?.id).toBe(week.id);
      expect(home.week?.research_day).toBe(day);
      expect(home.clock.slot).toBe("morning");
      expect(home.fly?.stage).toBe(stages[day - 2]);
      await expect(page.getByRole("heading", { level: 1 })).toContainText(`研究${day}日目`);
      // Four real 30s meals keep this representative loop within 2–4 minutes.
      // Missing other meals is valid gameplay; rank and random rewards are not fixed.
      if ([2, 4, 7].includes(day)) await playMeal(page);
      if (day === 2 || day === 4) await playTraining(page, day === 2 ? 5 : 6);
      if (day <= 5) await playCleaning(page);
      if (day === 5) {
        await advanceTime(page, "next_slot");
        const night = await advanceTime(page, "next_slot");
        expect(night.clock.slot).toBe("night");
        await choosePupationSite(page);
      }
      if (day === 6) await playTemperature(page);
    });
  }

  await test.step("day 7 night: presentation and eclosion", async () => {
    const night = await advanceTime(page, "eclosion");
    expect(night.week?.research_day).toBe(7);
    expect(night.clock.slot).toBe("night");
    expect(night.week?.ready_to_eclose).toBe(true);
    const presentation = await apiAction<Schemas["Presentation"]>(page,
      "/v1/weeks/current/presentation", "GET", () =>
        page.getByRole("link", { name: /研究発表会へ/ }).click());
    expect(presentation.meal_points).toBeGreaterThan(0);
    expect(presentation.training_points).toBeGreaterThan(0);
    expect(presentation.care_points).toBeGreaterThan(0);
    await expect(page.getByRole("heading", { name: "研究発表会", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "羽化を見る", exact: true }).click();
    const result = await apiAction<Schemas["Eclosion"]>(page,
      "/v1/weeks/current/eclose", "POST", () =>
        page.getByRole("button", { name: "羽化させる", exact: true }).click());
    expect(result.adult.id).toBeTruthy();
    await page.getByRole("button", { name: "飼育室へ", exact: true }).click({ timeout: 30_000 });
    await expect(page).toHaveURL(new RegExp(`/adults/${result.adult.id}$`));
    await expect(page.getByRole("heading", { level: 2 }).filter({ hasText: result.adult.name })).toBeVisible();

    const adult = await apiAction<Schemas["Adult"]>(page, `/v1/adults/${result.adult.id}`, "GET", () => page.reload());
    expect(adult.week_id).toBe(week.id);
    expect(adult.stars).toBe(result.adult.stars);
    const adults = await apiAction<Schemas["Adult"][]>(page, "/v1/adults", "GET", () => page.goto("/team"));
    expect(adults.some(fly => fly.id === result.adult.id)).toBe(true);
    await expect(page.getByRole("heading", { name: "研究チーム", exact: true })).toBeVisible();
    await expect(page.locator(`a[href="/adults/${result.adult.id}"]`)).toBeVisible();
    await page.locator(`a[href="/adults/${result.adult.id}"]`).click();
    await expect(page).toHaveURL(new RegExp(`/adults/${result.adult.id}$`));
    await expect(page.getByRole("heading", { level: 2 }).filter({ hasText: result.adult.name })).toBeVisible();
  });

  const home = await apiAction<Schemas["HomeData"]>(page, "/v1/home", "GET", () => page.goto("/"));
  expect(home.week).toBeNull();
  await expect(page.getByRole("button", { name: "卵を受け取る", exact: true })).toBeEnabled();
});
