import { expect, test } from "@playwright/test";
import { openGuestHome, readHome, receiveEgg } from "./helpers/session";

test("guest home renders and an egg starts a persisted research week", async ({ page }) => {
  await openGuestHome(page);
  const week = await receiveEgg(page);
  const home = await readHome(page);
  expect(home.week?.id).toBe(week.id);
  expect(home.week?.research_day).toBe(1);
  // Day one hatches at night, so this smoke test also works after 18:00 JST.
  expect(["egg", "larva1"]).toContain(home.fly?.stage);
  await expect(page.locator('a[href="/care/temperature"]')).toBeVisible();
});
