import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { EvidenceChips } from "./EvidenceChips";

describe("answer evidence disclosure", () => {
  it("shows six chips and keeps remaining evidence inside a closed native disclosure", () => {
    const evidence = Array.from({ length: 46 }, (_, i) => `#${String(i + 1).padStart(4, "0")}`);
    const html = renderToStaticMarkup(createElement(EvidenceChips, { evidence }));
    const [visible, hidden] = html.split("<details>");
    expect(visible.match(/<span /g)).toHaveLength(6);
    expect(visible).toContain("#0006");
    expect(visible).not.toContain("#0007");
    expect(hidden).toContain("+40件");
    expect(hidden).toContain("#0046");
    expect(html).not.toContain(" open=");
  });

  it("omits expansion for six or fewer unique IDs and handles no evidence", () => {
    const html = renderToStaticMarkup(createElement(EvidenceChips, { evidence: ["#0001", "#0001", "#c-1"] }));
    expect(html.match(/<span /g)).toHaveLength(2);
    expect(html).not.toContain("<details");
    expect(renderToStaticMarkup(createElement(EvidenceChips, { evidence: [] }))).toBe("");
  });
});
