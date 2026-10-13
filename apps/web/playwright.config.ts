import { defineConfig, devices } from "@playwright/test";

const software = process.env.E2E_SOFTWARE_WEBGL === "1";

// Software WebGL can spend seconds per frame; retain normal deadlines on hardware.
// Start the real API/worker and web separately; discovery needs no running services.
export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  testIgnore: "**/capture.spec.ts",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: software ? 60_000 : 15_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  outputDir: "test-results",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    actionTimeout: software ? 60_000 : 15_000,
    navigationTimeout: software ? 60_000 : 30_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: software ? "off" : "retain-on-failure",
    timezoneId: "Asia/Tokyo",
    locale: "ja-JP",
    launchOptions: process.env.E2E_SOFTWARE_WEBGL === "1" ? { args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } : undefined,
  },
  projects: [{
    name: "chromium",
    use: { ...devices["Desktop Chrome"], viewport: { width: 1100, height: 1000 } },
  }],
});
