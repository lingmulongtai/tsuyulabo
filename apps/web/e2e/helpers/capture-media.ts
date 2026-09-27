import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";
import { expect, type Page } from "@playwright/test";

export const mediaRoot = path.resolve(__dirname, "../../../..", "docs/media");
export const rawRoot = path.resolve(mediaRoot, "../../eval-results/media");

/** Both themes show the same real game state; only browser color preference changes. */
export class MediaCapture {
  readonly shots: string[] = [];
  readonly chapters: { name: string; seconds: number }[] = [];
  private started = Date.now();

  async prepare(page: Page) {
    await mkdir(path.join(mediaRoot, "screens"), { recursive: true });
    await mkdir(rawRoot, { recursive: true });
    this.started = Date.now();
    // Hide development chrome in portfolio media, preserving the real controls for time travel.
    await page.addInitScript(() => {
      const style = document.createElement("style");
      style.textContent = 'nextjs-portal { display: none !important; } aside[aria-label="開発用の時間操作"] { opacity: 0; } aside[aria-label="開発用の時間操作"]:focus-within { opacity: 1; }';
      document.addEventListener("DOMContentLoaded", () => document.head.append(style));
    });
    await page.clock.install();
  }

  async shot(page: Page, name: string, { paused = false, top = true } = {}) {
    if (this.shots.includes(name)) return;
    if (!paused) await page.clock.pauseAt(await page.evaluate(() => Date.now() + 100));
    if (top) await page.evaluate(() => window.scrollTo(0, 0));
    await page.evaluate(() => document.fonts.ready);
    this.chapters.push({ name, seconds: (Date.now() - this.started) / 1000 });
    for (const colorScheme of ["light", "dark"] as const) {
      await page.emulateMedia({ colorScheme });
      const png = await page.screenshot({ animations: "allow", caret: "hide" });
      let encoded: Buffer = Buffer.alloc(0);
      for (const quality of [80, 72, 64, 56]) {
        encoded = await sharp(png).webp({ quality, effort: 6 }).toBuffer();
        if (encoded.length < 150_000) break;
      }
      expect(encoded.length, `${name}-${colorScheme} budget`).toBeLessThan(150_000);
      await writeFile(path.join(mediaRoot, "screens", `${name}-${colorScheme}.webp`), encoded);
    }
    await page.emulateMedia({ colorScheme: "light" });
    this.shots.push(name);
    if (!paused) await page.clock.resume();
  }

  async finish(summary: object) {
    expect(this.shots).toHaveLength(13);
    await writeFile(path.join(rawRoot, "capture.json"), JSON.stringify({
      viewport: { width: 390, height: 844, deviceScaleFactor: 2 },
      ...summary, shots: this.shots, chapters: this.chapters,
    }, null, 2) + "\n");
  }
}
