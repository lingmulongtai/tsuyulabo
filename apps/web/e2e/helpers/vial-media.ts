import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { expect, type Page } from "@playwright/test";
import sharp from "sharp";

/** Actual game renders, captured only after the lazy renderer draws its first frame. */
export async function captureVial(page: Page, name: string, selector: string) {
  const surface = page.locator(selector).first();
  await expect(surface).toBeVisible();
  await expect(surface.locator("canvas[data-ready='true']")).toBeVisible({ timeout: 30_000 });
  const folder = process.env.E2E_MEDIA_DIR ?? resolve(process.cwd(), "../../docs/media/v2");
  await mkdir(folder, { recursive: true });
  // The scene keeps drawing. Capture its fixed container without waiting for two
  // compositor frames, which can take over 15s on a software-only renderer.
  await surface.evaluate(element => element.scrollIntoView({ block: "center", behavior: "instant" }));
  const clip = await surface.boundingBox();
  if (!clip || clip.width <= 0 || clip.height <= 0) throw new Error("Vial has no capture bounds");
  const render = await page.screenshot({ clip, animations: "disabled", timeout: 60_000 });
  await sharp(render).webp({ quality: 85 }).toFile(resolve(folder, `integrate-${name}.webp`));
}
