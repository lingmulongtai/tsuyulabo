import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { WeekStrip } from "./WeekStrip";
describe("weekly growth line", () => {
  it("labels all seven days and marks only the current day", () => {
    const html = renderToStaticMarkup(<WeekStrip researchDay={4} />);
    expect(html.match(/<li /g)).toHaveLength(7);
    expect(html.match(/aria-current="date"/g)).toHaveLength(1);
    expect(html).toContain('aria-current="date" aria-label="4日目（木）"');
    expect(html).toContain("7日目（日）・羽化");
  });
});
