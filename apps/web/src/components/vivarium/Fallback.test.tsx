import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import { Fallback } from "./Fallback";
it("distinguishes a loading preview from a terminal stage fallback", () => {
  const loading = renderToStaticMarkup(<Fallback loading />);
  const failed = renderToStaticMarkup(<Fallback stage="egg" />);
  expect(loading).toContain('data-vivarium-loading="true"');
  expect(failed).not.toContain("data-vivarium-loading");
  expect(failed).toContain("fallback-egg.webp");
});
