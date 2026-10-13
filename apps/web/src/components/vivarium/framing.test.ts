import { expect, it } from "vitest";
import { stageFraming } from "./framing";
it("keeps every immature stage visible and gives adults more space", () => {
  for (const stage of ["egg", "larva", "larva1", "larva2", "larva3", "wandering", "pupa"] as const) expect(stageFraming(stage)).toBe("close");
  expect(stageFraming("adult")).toBe("habitat");
});
