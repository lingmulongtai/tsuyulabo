import { expect, it } from "vitest";
import { bagCapacity, notificationText, preferencePercent, shioriAnswer } from "./display";

it("maps bounded preferences around a neutral midpoint", () => {
  expect([-2, -1, 0, 0.6, 1, 2, NaN].map(preferencePercent)).toEqual([0, 0, 50, 80, 100, 100, 50]);
});
it("stacks repeated bag subskills, matching independent server rolls", () => {
  expect(bagCapacity([])).toBe(30);
  expect(bagCapacity(["bag_up", "gather_s", "bag_up"])).toBe(50);
});
it("handles unknown notification payloads without leaking objects into the UI", () => {
  const base = { id: "n", created_at: "2026-09-27", read_at: null };
  expect(notificationText({ ...base, kind: "gift", payload: { display_name: "ゆうき", material: "banana", amount: 3 } })).toContain("バナナを3個");
  expect(notificationText({ ...base, kind: "unknown", payload: {} })).toContain("お知らせ");
});
it("reads an answer without inventing evidence", () => {
  expect(shioriAnswer({ answer: "観察しました", evidence: ["event#1", {}, 2] })).toEqual({ answer: "観察しました", evidence: ["event#1"] });
  expect(shioriAnswer(null)).toEqual({ answer: null, evidence: [] });
});

it("explains mating notifications and where to find the egg", () => {
  const base = { id: "n", created_at: "2026-09-27", read_at: null, payload: {} };
  expect(notificationText({ ...base, kind: "mating_pending" })).toContain("申込");
  expect(notificationText({ ...base, kind: "mating_accepted" })).toContain("ホーム");
  expect(notificationText({ ...base, kind: "mating_declined" })).toContain("辞退");
});
