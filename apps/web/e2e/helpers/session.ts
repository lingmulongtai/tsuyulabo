import { expect, type Page, type Request } from "@playwright/test";
import type { components } from "../../src/lib/api/schema";

export type Schemas = components["schemas"];
const apiBase = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// Observe the application's request, never replace responses or submit care through an API client.
export async function apiAction<T>(page: Page, path: string, method: string, action: () => Promise<unknown>) {
  // Observe new requests only, including the client's automatic retry of the same action.
  // Mutation retries must keep the original idempotency key. Never accept a different action.
  let first = true;
  let key: string | undefined;
  let observe: (request: Request) => void;
  let timeout: ReturnType<typeof setTimeout> | undefined;
  const pending = new Promise<T>((resolve, reject) => {
    timeout = setTimeout(() => reject(new Error(`${method} ${path} did not receive a response`)), 30_000);
    observe = request => {
      if (request.url() !== `${apiBase}${path}` || request.method() !== method) return;
      const requestKey = request.headers()["idempotency-key"];
      if (first) { first = false; key = requestKey; }
      if (requestKey !== key) return;
      void (async () => {
        try {
          const response = await request.response();
          if (!response) return; // Transport may automatically resend a timed-out request.
          expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBeTruthy();
          // Read immediately so a subsequent navigation cannot discard the body.
          resolve(await response.json() as T);
        } catch (error) { reject(error); }
      })();
    };
  });
  page.on("request", observe!);
  try {
    const [data] = await Promise.all([pending, action()]);
    return data;
  } finally {
    clearTimeout(timeout);
    page.off("request", observe!);
  }
}

export async function openGuestHome(page: Page) {
  const guest = await apiAction<Schemas["Guest"]>(page, "/v1/auth/guest", "POST", () => page.goto("/"));
  expect(guest.user.id).toBeTruthy();
  await expect(page.getByRole("heading", { name: "ツユラボ", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "卵を受け取る", exact: true })).toBeEnabled();
}

export async function receiveEgg(page: Page) {
  const week = await apiAction<Schemas["Week"]>(page, "/v1/weeks", "POST", () =>
    page.getByRole("button", { name: "卵を受け取る", exact: true }).click());
  expect(week.id).toBeTruthy();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("1日目");
  await expect(page.getByRole("button", { name: "卵を受け取る", exact: true })).toHaveCount(0);
  return week;
}

export async function readHome(page: Page) {
  return apiAction<Schemas["HomeData"]>(page, "/v1/home", "GET", () => page.reload());
}

export async function advanceTime(page: Page, target: "next_slot" | "next_day" | "eclosion") {
  const panel = page.getByRole("complementary", { name: "開発用の時間操作" });
  await expect(panel, "Build the web with NEXT_PUBLIC_DEV_TOOLS=1").toBeVisible();
  const toggle = panel.getByRole("button", { name: /開発用の時計/ });
  if (await toggle.getAttribute("aria-expanded") !== "true") await toggle.click();
  const labels = { next_slot: "次の時間帯", next_day: "次の日", eclosion: "羽化の夜へ" };
  await apiAction(page, "/v1/dev/time/advance", "POST", () =>
    panel.getByRole("button", { name: labels[target], exact: true }).click());
  await toggle.click();
  return readHome(page);
}

export async function returnHome(page: Page) {
  await page.getByRole("link", { name: "ホームへ", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/\d日目/);
}
