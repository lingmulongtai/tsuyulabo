import { describe, expect, it, vi } from "vitest";
import { ApiError, createAction, createApi, parseApiError, TOKEN_KEY, unwrap } from "./client";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const memory = (initial?: string) => {
  const values = new Map(initial ? [[TOKEN_KEY, initial]] : []);
  return { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => { values.set(key, value); } };
};

describe("api client", () => {
  it("bootstraps once for concurrent reads and stores the bearer token", async () => {
    const storage = memory();
    const fetcher = vi.fn<typeof fetch>(async (input) => {
      const req = input as Request;
      if (req.url.endsWith("/auth/guest")) {
        expect(req.headers.get("Idempotency-Key")).toMatch(/^[\da-f-]{36}$/);
        return json({ token: "guest-token" }, 201);
      }
      expect(req.headers.get("Authorization")).toBe("Bearer guest-token");
      return json({});
    });
    const { client } = createApi({ fetch: fetcher, storage: () => storage });
    await Promise.all([client.GET("/v1/home"), client.GET("/v1/me")]);
    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(storage.getItem(TOKEN_KEY)).toBe("guest-token");
  });

  it("keeps one key across automatic and manual retries, then creates a new action key", async () => {
    const requests: Request[] = [];
    const fetcher = vi.fn<typeof fetch>(async (input) => {
      requests.push(input as Request);
      if (requests.length < 3) throw new TypeError("lost response");
      return json({});
    });
    const { client } = createApi({ fetch: fetcher, storage: () => memory("saved") });
    const action = createAction(headers => unwrap(client.POST("/v1/weeks", { headers })));
    await expect(action.run()).rejects.toMatchObject({ code: "offline" });
    await action.run();
    await createAction(headers => unwrap(client.POST("/v1/weeks", { headers }))).run();
    expect(new Set(requests.slice(0, 3).map(r => r.headers.get("Idempotency-Key"))).size).toBe(1);
    expect(requests[3].headers.get("Idempotency-Key")).not.toBe(action.key);
  });

  it("parses API details without retrying rule errors", async () => {
    const fetcher = vi.fn<typeof fetch>(async () => json({ error: { code: "slot_already_used", message: "お世話は済んでいます", details: { slot: "noon" } } }, 409));
    const { client } = createApi({ fetch: fetcher, storage: () => memory("saved") });
    await expect(client.POST("/v1/weeks")).rejects.toMatchObject({ status: 409, code: "slot_already_used", details: { slot: "noon" } });
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(parseApiError(502, "<html>")).toBeInstanceOf(ApiError);
    expect(parseApiError(422, { detail: [] }).code).toBe("validation_error");
  });

  it("keeps an in-memory token when storage is blocked", async () => {
    const fetcher = vi.fn<typeof fetch>(async () => json({ token: "memory" }, 201));
    const { getToken } = createApi({ fetch: fetcher, storage: () => { throw new Error("denied"); } });
    expect(await getToken()).toBe("memory");
    expect(await getToken()).toBe("memory");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("does not create a guest during SSR", async () => {
    const fetcher = vi.fn<typeof fetch>();
    await expect(createApi({ fetch: fetcher }).getToken()).rejects.toMatchObject({ code: "client_only" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("retains bootstrap identity across a failed attempt and explicit retry", async () => {
    const keys: (string | null)[] = [];
    const fetcher = vi.fn<typeof fetch>(async input => {
      keys.push((input as Request).headers.get("Idempotency-Key"));
      if (keys.length === 1) return json({ error: { code: "busy", message: "混雑中" } }, 503);
      return json({ token: "recovered" }, 201);
    });
    const { getToken } = createApi({ fetch: fetcher, storage: () => memory(), retries: 0 });
    await expect(getToken()).rejects.toMatchObject({ status: 503 });
    expect(await getToken()).toBe("recovered");
    expect(keys[0]).toBe(keys[1]);
  });

  it("preserves a saved identity on unauthorized responses", async () => {
    const storage = memory("expired");
    const fetcher = vi.fn<typeof fetch>(async () => json({ error: { code: "unauthorized", message: "期限切れ" } }, 401));
    const { client } = createApi({ fetch: fetcher, storage: () => storage });
    await expect(client.GET("/v1/me")).rejects.toMatchObject({ code: "unauthorized" });
    expect(storage.getItem(TOKEN_KEY)).toBe("expired");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("retries server failures with the same serialized mutation body", async () => {
    const bodies: unknown[] = [];
    const keys: (string | null)[] = [];
    const fetcher = vi.fn<typeof fetch>(async input => {
      const request = input as Request;
      bodies.push(await request.json());
      keys.push(request.headers.get("Idempotency-Key"));
      return bodies.length === 1 ? new Response("gateway unavailable", { status: 502 }) : json({});
    });
    const { client } = createApi({ fetch: fetcher, storage: () => memory("saved") });
    await client.PUT("/v1/team", { body: { adult_ids: ["a1"] } });
    expect(bodies).toEqual([{ adult_ids: ["a1"] }, { adult_ids: ["a1"] }]);
    expect(keys[0]).toBe(keys[1]);
  });

  it("rejects malformed bootstrap data without saving an invalid token", async () => {
    const storage = memory();
    const { getToken } = createApi({ fetch: vi.fn<typeof fetch>(async () => json({ token: 123 })), storage: () => storage });
    await expect(getToken()).rejects.toMatchObject({ code: "invalid_response" });
    expect(storage.getItem(TOKEN_KEY)).toBeNull();
  });
});
