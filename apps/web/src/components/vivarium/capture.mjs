// Run from repo root against `npm.cmd run start -w apps/web -- --port 3015`.
import { chromium } from "@playwright/test";
import sharp from "sharp";
import { mkdir, writeFile } from "node:fs/promises";
import assert from "node:assert/strict";

const base = process.env.VIVARIUM_URL ?? "http://127.0.0.1:3015";
const browser = await chromium.launch({ headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const errors = [], report = { renderer: "", captures: [], checks: [], performance: [] };
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 1, reducedMotion: "reduce" });
page.on("pageerror", error => errors.push(String(error)));
page.on("console", message => { if (message.type() === "error" && /THREE|WebGL|shader/i.test(message.text())) errors.push(message.text()); });
const media = "docs/media/v2", assets = "apps/web/public/vivarium";
await mkdir(media, { recursive: true });
await mkdir(assets, { recursive: true });
async function ready(url) {
  await page.goto(base + url, { waitUntil: "networkidle", timeout: 120000 });
  await page.locator("canvas[data-ready=true]").waitFor({ timeout: 120000 });
}
try {
  for (const stage of process.env.VIVARIUM_SKIP_CAPTURES ? [] : ["adult", "egg", "larva", "pupa"]) for (const framing of ["wide", "close"]) {
    await ready(`/vivarium?stage=${stage}&framing=${framing}&quality=high&paused=1&clean=1`);
    const png = await page.screenshot();
    const file = `${media}/vivarium-${stage}-${framing}.webp`;
    await sharp(png).webp({ quality: 91 }).toFile(file);
    if (framing === "close") await sharp(png).resize(1000).webp({ quality: 83 }).toFile(`${assets}/fallback-${stage}.webp`);
    report.captures.push(file); console.log(file);
    const stats = await sharp(png).stats(); assert(stats.entropy > 3, `${stage}: blank capture`);
  }
  if (process.env.VIVARIUM_SKIP_CAPTURES) await ready("/vivarium?stage=pupa&framing=close&quality=high&paused=1&clean=1");
  await page.emulateMedia({ colorScheme: "light" }); const light = await page.screenshot();
  await page.emulateMedia({ colorScheme: "dark" }); const dark = await page.screenshot();
  const a = await sharp(light).removeAlpha().raw().toBuffer(), b = await sharp(dark).removeAlpha().raw().toBuffer();
  let difference = 0; for (let i = 0; i < a.length; i++) difference += Math.abs(a[i] - b[i]);
  assert(difference / a.length < 3, "system theme altered the scene");
  report.checks.push({ themeMeanChannelDifference: difference / a.length });

  await page.setViewportSize({ width: 390, height: 844 });
  await ready("/vivarium?quality=low&behaviour=rest");
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "mobile overflow");
  await page.locator("summary").click();
  for (const action of ["walk", "turn_left", "turn_right", "feed", "groom", "escape", "approach", "avoid", "fly", "rest"]) {
    await page.getByLabel("行動", { exact: true }).selectOption(action);
    await page.waitForFunction(value => document.querySelector("canvas")?.dataset.behaviour === value, action);
  }
  await page.getByRole("button", { name: "奥に匂いを置く" }).click();
  await page.getByLabel("行動", { exact: true }).selectOption("feed");
  await page.waitForFunction(() => document.querySelector("canvas")?.dataset.behaviour === "feed");
  await page.getByRole("button", { name: "一時停止" }).click();
  const pausedPhase = await page.locator("canvas").getAttribute("data-phase");
  await page.getByLabel("湿度", { exact: true }).fill("0.9");
  assert.equal(await page.locator("canvas").getAttribute("data-phase"), pausedPhase, "pause moved the animal");
  await page.screenshot({ path: ".codex-runs/vivarium-mobile.png" });
  report.checks.push("390px layout, decoder actions, imperative then controlled action, pause while changing humidity");

  await page.emulateMedia({ reducedMotion: "no-preference" });
  for (const quality of ["low", "medium", "high"]) {
    await ready(`/vivarium?quality=${quality}&behaviour=walk&clean=1`);
    await page.waitForFunction(() => Number(document.querySelector("canvas")?.dataset.phase) > 2, null, { timeout: 120000 });
    await page.waitForFunction(() => Boolean(document.querySelector("canvas")?.dataset.fps), null, { timeout: 120000 });
    const data = await page.locator("canvas").evaluate(canvas => {
      const gl = canvas.getContext("webgl2"), ext = gl.getExtension("WEBGL_debug_renderer_info");
      return { ...canvas.dataset, renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : "unknown" };
    });
    const timings = await page.evaluate(() => new Promise(resolve => {
      const samples = []; let previous;
      function frame(time) {
        if (previous !== undefined) samples.push(time - previous);
        previous = time;
        if (samples.length < 75) requestAnimationFrame(frame);
        else {
          const measured = samples.slice(15), sorted = [...measured].sort((a, b) => a - b);
          resolve({ frames: measured.length, meanFps: 1000 / (measured.reduce((a, b) => a + b, 0) / measured.length), p95Ms: sorted[Math.floor(sorted.length * 0.95)] });
        }
      }
      requestAnimationFrame(frame);
    }));
    report.renderer = data.renderer; report.performance.push({ quality, viewport: "390x844", ...data, timings }); console.log(report.performance.at(-1));
  }
  // Context-loss path uses the actual browser WebGL event and returns a valid static image.
  await page.locator("canvas").evaluate(canvas => canvas.getContext("webgl2").getExtension("WEBGL_lose_context").loseContext());
  await page.locator("[data-vivarium-fallback]").waitFor();
  await page.waitForFunction(() => { const image = document.querySelector("[data-vivarium-fallback] img"); return image?.complete && image.naturalWidth > 0; });
  report.checks.push("context loss shows a decoded static render");
  const unsupported = await chromium.launch({ headless: true, args: ["--disable-webgl", "--disable-webgl2"] });
  try {
    const fallbackPage = await unsupported.newPage();
    await fallbackPage.goto(base + "/vivarium?stage=egg", { waitUntil: "networkidle" });
    await fallbackPage.waitForFunction(() => { const image = document.querySelector("[data-vivarium-fallback] img"); return image?.complete && image.naturalWidth > 0; });
    assert.equal(await fallbackPage.locator("canvas[data-ready=true]").count(), 0);
    report.checks.push("WebGL unavailable shows the egg static render");
  } finally { await unsupported.close(); }
  assert.deepEqual(errors, []);
  await writeFile(".codex-runs/vivarium-report.json", JSON.stringify(report, null, 2));
} finally { await writeFile(".codex-runs/vivarium-report.json", JSON.stringify(report, null, 2)); await browser.close(); }
