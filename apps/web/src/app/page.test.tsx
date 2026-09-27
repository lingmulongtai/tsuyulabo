import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import Home from "./page";

const { useHome } = vi.hoisted(() => ({ useHome: vi.fn(() => { throw new Error("live home mounted"); }) }));
vi.mock("@/lib/api/hooks", () => ({ useHome, useStartWeek: vi.fn() }));
vi.mock("@/components/shell/DevTimePanel", () => ({ DevTimePanel: () => null }));

afterEach(() => { vi.unstubAllEnvs(); vi.clearAllMocks(); });

describe("public demo home", () => {
  it("renders offline activities without starting a home query", () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    const html = renderToStaticMarkup(createElement(Home));
    expect(html).toContain("公開デモ");
    for (const href of ["/care/meal?practice=1", "/care/training?practice=1", "/eclosion?demo=1", "/presentation?demo=1"]) {
      expect(html).toContain(`href="${href}"`);
    }
    expect(useHome).not.toHaveBeenCalled();
  });

  it.each([
    ["production", "https://api.example.com"],
    ["development", ""],
  ])("keeps live home for %s with API URL %s", (mode, url) => {
    vi.stubEnv("NODE_ENV", mode);
    vi.stubEnv("NEXT_PUBLIC_API_URL", url);
    expect(() => renderToStaticMarkup(createElement(Home))).toThrow("live home mounted");
    expect(useHome).toHaveBeenCalledOnce();
  });
});
