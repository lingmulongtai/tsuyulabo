import { describe, expect, it, vi } from "vitest";
vi.mock("../vivarium/Vivarium", () => ({ Vivarium: () => null }));
import { momentProps } from "./DiaryMoment";
import type { DiaryEntry } from "./hooks";

const moment: DiaryEntry["snapshot"] = { record_id: "#0001", at: "2026-10-13T00:00:00Z", seed: "individual", stage: "adult", behaviour: "approach", environment: {}, sex: "m", phenotypes: ["white", "curly"] };
describe("diary 3D moment", () => {
  it("replays the recorded stage, action and adult morphology", () => {
    expect(momentProps(moment)).toMatchObject({ seed: "individual", stage: "adult", behaviour: "approach", sex: "m", traits: ["white", "curly"] });
  });
  it("handles older or unknown snapshot vocabulary without fabricating traits", () => {
    expect(momentProps({ ...moment, stage: "unknown", behaviour: "unknown", sex: null, phenotypes: ["unknown"] })).toMatchObject({ stage: "egg", behaviour: "rest", sex: undefined, traits: [] });
  });
});
