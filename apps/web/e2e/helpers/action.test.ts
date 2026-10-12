import { expect, it } from "vitest";
import type { Page, Request } from "@playwright/test";
import { apiAction } from "./session";

function fixture() {
  const observers = new Set<(request: Request) => void>();
  const page = {
    on: (_event: string, handler: (request: Request) => void) => observers.add(handler),
    off: (_event: string, handler: (request: Request) => void) => observers.delete(handler),
  } as unknown as Page;
  const send = (key: string, result: unknown, status = 200) => {
    const request = {
      url: () => "http://localhost:8000/v1/puzzles/p/submit",
      method: () => "POST",
      headers: () => ({ "idempotency-key": key }),
      response: async () => result === null ? null : {
        ok: () => status >= 200 && status < 300,
        text: async () => JSON.stringify(result),
        json: async () => result,
      },
    } as unknown as Request;
    for (const observe of observers) observe(request);
  };
  return { page, send, observers };
}

it("waits for the real response after an automatic retry with the same key", async () => {
  const { page, send, observers } = fixture();
  const result = await apiAction(page, "/v1/puzzles/p/submit", "POST", async () => {
    send("original", null);
    await Promise.resolve();
    send("original", { score: 100 });
  });
  expect(result).toEqual({ score: 100 });
  expect(observers.size).toBe(0);
});

it("ignores old requests and responses to a different mutation key", async () => {
  const { page, send } = fixture();
  send("older", { score: 1 });
  const result = await apiAction(page, "/v1/puzzles/p/submit", "POST", async () => {
    send("original", null);
    send("other-action", { score: 2 });
    send("original", { score: 100 });
  });
  expect(result).toEqual({ score: 100 });
});

it("still rejects server validation failures instead of hiding them with later successes", async () => {
  const { page, send, observers } = fixture();
  await expect(apiAction(page, "/v1/puzzles/p/submit", "POST", async () => {
    send("original", { error: "invalid input" }, 422);
  })).rejects.toThrow("invalid input");
  expect(observers.size).toBe(0);
});

it("removes the observer when the UI action fails", async () => {
  const { page, observers } = fixture();
  await expect(apiAction(page, "/v1/puzzles/p/submit", "POST", async () => {
    throw new Error("control unavailable");
  })).rejects.toThrow("control unavailable");
  expect(observers.size).toBe(0);
});
