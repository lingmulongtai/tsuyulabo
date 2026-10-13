import { describe, expect, it } from "vitest";
import { shareText, wrapCardText } from "./share-card";

describe("diary share card", () => {
  it("keeps diary prose while hiding internal evidence ids", () => {
    expect(shareText("ごはんを入れました #0001。羽化しました #c-2。" )).toBe("ごはんを入れました。羽化しました。");
  });
  it("wraps Japanese and emoji without losing characters", () => {
    const text = "この子が🪰羽化しました。";
    const lines = wrapCardText(text, 4, value => Array.from(value).length);
    expect(lines.join("")).toBe(text);
    expect(lines.every(line => Array.from(line).length <= 4)).toBe(true);
    expect(wrapCardText("朝\n夜", 10, value => value.length)).toEqual(["朝", "夜"]);
  });
});
