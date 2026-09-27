import type { CapacitorConfig } from "@capacitor/cli";

const appUrl = process.env.TSUYU_APP_URL ?? "https://tsuyulabo.vercel.app";
const parsedUrl = new URL(appUrl);
if (parsedUrl.protocol !== "https:") {
  throw new Error("TSUYU_APP_URL must use HTTPS");
}

const config: CapacitorConfig = {
  appId: "app.tsuyulabo.alpha",
  appName: "ツユラボ α",
  webDir: "www",
  server: {
    url: parsedUrl.toString(),
    errorPath: "offline.html",
  },
};

export default config;
