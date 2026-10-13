import { expect, it } from "vitest";
import { MomentClock } from "./moment-clock";

it("retains the remaining observation through pause or a hidden document", () => {
  const clock = new MomentClock(8000);
  clock.resume(100);
  expect(clock.advance(3100)).toBe(false);
  clock.suspend(4100);
  clock.resume(100_000);
  expect(clock.advance(103_999)).toBe(false);
  expect(clock.advance(104_000)).toBe(true);
});
it("starts a new full moment even when the next brain choice is the same", () => {
  const first = new MomentClock(8000);
  first.resume(0); expect(first.advance(8000)).toBe(true);
  const second = new MomentClock(8000);
  second.resume(8000); expect(second.advance(8001)).toBe(false);
  expect(second.advance(16_000)).toBe(true);
});
