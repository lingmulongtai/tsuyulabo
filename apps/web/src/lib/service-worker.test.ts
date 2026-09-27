import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { describe, expect, it, vi } from "vitest";

function worker() {
  const handlers: Record<string, (event: Record<string, unknown>) => void> = {};
  const cache = { add: vi.fn(), match: vi.fn().mockResolvedValue("offline") };
  const caches = { open: vi.fn().mockResolvedValue(cache), keys: vi.fn().mockResolvedValue(["tsuyu-offline-v0", "unrelated"]), delete: vi.fn() };
  const clients = { claim: vi.fn(), matchAll: vi.fn().mockResolvedValue([]), openWindow: vi.fn() };
  const showNotification = vi.fn();
  const fetch = vi.fn().mockRejectedValue(new Error("offline"));
  runInNewContext(readFileSync(new URL("../../public/sw.js", import.meta.url), "utf8"), {
    self: { addEventListener: (name: string, handler: typeof handlers[string]) => { handlers[name] = handler; },
      location: { origin: "https://tsuyu.test" }, clients, registration: { showNotification } },
    caches, fetch, URL, Response,
  });
  async function fire(name: string, event: Record<string, unknown> = {}) {
    let pending: Promise<unknown> | undefined;
    handlers[name]({ ...event, waitUntil: (promise: Promise<unknown>) => { pending = promise; } });
    await pending;
  }
  return { handlers, cache, caches, clients, showNotification, fetch, fire };
}

describe("service worker", () => {
  it("precaches only the offline page and deletes only its old caches", async () => {
    const sw = worker();
    await sw.fire("install");
    expect(sw.cache.add).toHaveBeenCalledWith("/offline.html");
    await sw.fire("activate");
    expect(sw.caches.delete).toHaveBeenCalledExactlyOnceWith("tsuyu-offline-v0");
    expect(sw.clients.claim).toHaveBeenCalledOnce();
  });

  it("falls back on offline navigation but never intercepts API requests or mutations", async () => {
    const sw = worker();
    const respondWith = vi.fn();
    sw.handlers.fetch({ request: { method: "GET", mode: "navigate", url: "https://tsuyu.test/care/meal" }, respondWith });
    expect(await respondWith.mock.calls[0][0]).toBe("offline");
    respondWith.mockClear();
    for (const request of [
      { method: "POST", mode: "navigate", url: "https://tsuyu.test/v1/puzzles" },
      { method: "GET", mode: "cors", url: "https://tsuyu.test/v1/home" },
      { method: "GET", mode: "navigate", url: "https://api.test/v1/home" },
    ]) sw.handlers.fetch({ request, respondWith });
    expect(respondWith).not.toHaveBeenCalled();
  });

  it("shows meal reminders and focuses their destination", async () => {
    const sw = worker();
    await sw.fire("push", { data: { json: () => ({ title: "ごはんの時間です", url: "/care/meal", tag: "meal:1" }) } });
    expect(sw.showNotification).toHaveBeenCalledWith("ごはんの時間です", expect.objectContaining({ data: { url: "/care/meal" }, tag: "meal:1" }));
    const focus = vi.fn();
    const navigate = vi.fn().mockResolvedValue({ focus });
    sw.clients.matchAll.mockResolvedValue([{ url: "https://tsuyu.test/", navigate }]);
    await sw.fire("notificationclick", { notification: { close: vi.fn(), data: { url: "/presentation" } } });
    expect(navigate).toHaveBeenCalledWith("https://tsuyu.test/presentation");
    expect(focus).toHaveBeenCalledOnce();
  });

  it("handles malformed data and refuses off-origin click targets", async () => {
    const sw = worker();
    await sw.fire("push", { data: { json: () => { throw new Error("invalid JSON"); } } });
    expect(sw.showNotification).toHaveBeenCalledOnce();
    await sw.fire("notificationclick", { notification: { close: vi.fn(), data: { url: "https://evil.test" } } });
    expect(sw.clients.openWindow).toHaveBeenCalledWith("https://tsuyu.test/");
  });
});
