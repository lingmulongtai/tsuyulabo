import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { CircadianCard } from "./CircadianCard";
import { CircadianRing } from "./CircadianRing";

describe("circadian display", () => {
  it("shows an empty history without inventing typical times", () => {
    const html = renderToStaticMarkup(createElement(CircadianCard, {
      circadian: { gauge: 0, streak: 0, typical_bedtime: null, typical_wake: null },
    }));
    expect(html).toContain('aria-valuenow="0"');
    expect(html).toContain("いつもの時間はまだありません");
    expect(html).not.toContain("23:00");
  });

  it("renders server times, streak, and separates game rewards from biology", () => {
    const html = renderToStaticMarkup(createElement(CircadianCard, {
      circadian: { gauge: 86, streak: 6, typical_bedtime: "00:05", typical_wake: "08:05" },
    }));
    for (const text of ["00:05", "08:05", "6日連続", "本物", "ゲーム", "period", "timeless", "しずくが20", "<dialog"]) {
      expect(html).toContain(text);
    }
    expect(html).toContain('aria-valuenow="86"');
  });

  it("keeps compact rings accessible and gives multiple moons unique masks", () => {
    const html = renderToStaticMarkup(createElement("div", null,
      createElement(CircadianRing, { gauge: 100, compact: true }),
      createElement(CircadianRing, { gauge: 0 }),
    ));
    expect(html.match(/role="meter"/g)).toHaveLength(2);
    const ids = [...html.matchAll(/<mask id="([^"]+)"/g)].map(match => match[1]);
    expect(new Set(ids).size).toBe(2);
    expect(html).toContain('aria-label="体内時計ゲージ"');
    expect(html).toContain('stroke-dasharray="100 100"');
  });
});
