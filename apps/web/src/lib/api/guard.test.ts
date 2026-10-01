import { afterEach, expect, it, vi } from "vitest";
import { createApi, parseApiError, unwrap } from "./client";

afterEach(() => vi.useRealTimers());

it.each([[429, "rate_limited"], [503, "server_busy"]])("respects cooldown for %s without automatic or manual network retries", async (status, code) => {
  vi.useFakeTimers();
  const fetcher = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({ error: { code, message: "busy", details: { retry_after: 2 } } }), {
    status: Number(status), headers: { "Retry-After": "20" },
  }));
  const { client } = createApi({ fetch: fetcher, storage: () => ({ getItem: () => "token", setItem: () => {} }) });
  await expect(client.GET("/v1/me")).rejects.toMatchObject({ retryable: false, retryAfter: 20, message: "少し時間をおいてから、もう一度ためしてね。" });
  await expect(client.GET("/v1/me")).rejects.toMatchObject({ code });
  expect(fetcher).toHaveBeenCalledTimes(1);
  vi.advanceTimersByTime(20_000);
  await expect(client.GET("/v1/me")).rejects.toMatchObject({ code });
  expect(fetcher).toHaveBeenCalledTimes(2);
});

it("parses dates, malformed headers and details and preserves unwrap headers", async () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-01T00:00:00Z"));
  const body = { error: { code: "server_busy", message: "busy", details: { retry_after: 30 } } };
  expect(parseApiError(503, body, "Thu, 01 Oct 2026 00:01:00 GMT").retryAfter).toBe(60);
  expect(parseApiError(503, body, "invalid").retryAfter).toBe(30);
  expect(parseApiError(503, { error: { code: "server_busy", message: "busy" } }).retryAfter).toBe(10);
  await expect(unwrap(Promise.resolve({ error: body, response: new Response(null, { status: 503, headers: { "Retry-After": "60" } }) }))).rejects.toMatchObject({ retryAfter: 60 });
});
