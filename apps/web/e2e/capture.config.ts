import { defineConfig } from "@playwright/test";
import base from "../playwright.config";

// Explicit opt-in config: even `playwright test --project chromium` cannot record media.
export default defineConfig({
  ...base,
  testDir: ".",
  testMatch: "capture.spec.ts",
  testIgnore: [],
  timeout: 1_200_000,
  retries: 0,
  reporter: [["list"]],
  outputDir: "../../../eval-results/media/playwright",
  projects: [{
    name: "capture",
    use: {
      browserName: "chromium",
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 2,
      isMobile: true,
      colorScheme: "light",
      reducedMotion: "no-preference",
      video: { mode: "on", size: { width: 390, height: 844 } },
      trace: "retain-on-failure",
    },
  }],
});
