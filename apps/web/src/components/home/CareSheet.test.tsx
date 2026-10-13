import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import { CareSheet } from "./CareSheet";
it("keeps the full list out of the resting sheet and exposes its toggle", () => {
  const html = renderToStaticMarkup(<CareSheet preview={<p>次のお世話</p>}><p>全件</p></CareSheet>);
  expect(html).toContain('aria-expanded="false"');
  expect(html).toContain("次のお世話");
  expect(html).not.toContain("全件");
  expect(html).toContain("aria-controls=");
});
