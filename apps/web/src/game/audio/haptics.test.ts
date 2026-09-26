import { afterEach, expect, it, vi } from "vitest";
import { buzz } from "./haptics";

afterEach(() => { vi.unstubAllGlobals(); });

it("safely skips SSR and unsupported browsers", () => {
  vi.stubGlobal("navigator", undefined);
  expect(() => buzz(20)).not.toThrow();
  vi.stubGlobal("navigator", {});
  expect(() => buzz([25, 30, 25])).not.toThrow();
});

it("passes durations and copied patterns to the browser, including cancellation", () => {
  const vibrate = vi.fn();
  vi.stubGlobal("navigator", { vibrate });
  const pattern = [25, 30, 25] as const;
  buzz(20); buzz(pattern); buzz(0);
  expect(vibrate.mock.calls).toEqual([[20], [[25, 30, 25]], [0]]);
  expect(vibrate.mock.calls[1][0]).not.toBe(pattern);
});

it("ignores browser denial and exceptions", () => {
  vi.stubGlobal("navigator", { vibrate: () => false });
  expect(() => buzz(20)).not.toThrow();
  vi.stubGlobal("navigator", { vibrate: () => { throw new Error("denied"); } });
  expect(() => buzz(20)).not.toThrow();
});
