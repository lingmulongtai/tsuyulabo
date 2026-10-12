import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { EvidenceChips } from "./EvidenceChips";

describe("answer evidence disclosure", () => {
  it("keeps every reference inside a closed native disclosure", () => {
    const evidence = Array.from({ length: 46 }, (_, i) => `#${String(i + 1).padStart(4, "0")}`);
    const html = renderToStaticMarkup(createElement(EvidenceChips, { evidence }));
    expect(html).toMatch(/^<details/);
    const [visible, hidden] = html.split("</summary>");
    expect(visible).toContain("根拠");
    expect(visible).not.toContain("#0001");
    expect(hidden.match(/<span /g)).toHaveLength(46);
    expect(hidden).toContain("#0046");
    expect(html).not.toContain(" open=");
  });

  it("deduplicates short lists inside disclosure and handles no evidence", () => {
    const html = renderToStaticMarkup(createElement(EvidenceChips, { evidence: ["#0001", "#0001", "#c-1"] }));
    expect(html.match(/<span /g)).toHaveLength(2);
    expect(html).toContain("<details");
    expect(renderToStaticMarkup(createElement(EvidenceChips, { evidence: [] }))).toBe("");
  });
  it("keeps original quantitative text inside the disclosure without inventing IDs", () => {
    const html = renderToStaticMarkup(createElement(EvidenceChips, { evidence: [], detail: "好みの値は+0.57です。" }));
    const [visible, hidden] = html.split("</summary>");
    expect(visible).not.toContain("0.57");
    expect(hidden).toContain("+0.57");
    expect(html).not.toContain("<span");
  });
});
