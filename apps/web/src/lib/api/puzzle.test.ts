import { expect, it } from "vitest";
import { practiceCleaning, practiceMeal, practiceTemperature, practiceTraining } from "@/game/practice";
import { puzzleParams } from "./puzzle";

it("accepts engine-compatible issued params", () => {
  expect(puzzleParams("meal", practiceMeal(1)).rows).toBe(8);
  expect(puzzleParams("cleaning", practiceCleaning(1)).taps).toBe(3);
  expect(puzzleParams("temperature", practiceTemperature(1)).center_c).toBe(25);
  expect(puzzleParams("training", practiceTraining()).n).toBe(5);
  expect(puzzleParams("pupation_site", { hint: "乾いた場所", options: ["a", "b", "c"].map(id => ({ id, label: id, detail: "乾いている" })) }).options).toHaveLength(3);
});
it("rejects malformed or incompatible game params", () => {
  expect(() => puzzleParams("meal", { ...practiceMeal(1), pieces: [{ shape: "unknown", ingredient: "banana" }] })).toThrow();
  expect(() => puzzleParams("cleaning", { ...practiceCleaning(1), period_ms: 0 })).toThrow();
  expect(() => puzzleParams("temperature", { ...practiceTemperature(1), phase: NaN })).toThrow();
  expect(() => puzzleParams("pupation_site", null)).toThrow();
});
