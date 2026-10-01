import { describe, expect, it } from "vitest";
import { apiRewrites } from "./proxy";

describe("apiRewrites", () => {
  it("proxies nothing without a target", () => {
    expect(apiRewrites(undefined)).toEqual([]);
    expect(apiRewrites("  ")).toEqual([]);
  });

  it("forwards the API paths to the target origin", () => {
    expect(apiRewrites("https://ozg14.tail4204cd.ts.net/")).toEqual([
      { source: "/v1/:path*", destination: "https://ozg14.tail4204cd.ts.net/v1/:path*" },
      { source: "/healthz", destination: "https://ozg14.tail4204cd.ts.net/healthz" },
    ]);
  });

  it.each(["http://ozg14.tail4204cd.ts.net", "https://example.com/v1", "https://example.com/?a=1", "not a url"])(
    "rejects %s",
    (target) => expect(() => apiRewrites(target)).toThrow(),
  );
});
