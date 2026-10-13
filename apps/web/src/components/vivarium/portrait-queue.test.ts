import { describe, expect, it } from "vitest";
import { PortraitQueue } from "./portrait-queue";
describe("portrait snapshot queue", () => {
  it("renders one owner at a time and shares duplicate snapshots", () => {
    const queue = new PortraitQueue();
    queue.request("adult-a", "slot"); queue.request("adult-a", "card"); queue.request("adult-b", "next");
    expect(queue.active?.owner).toBe("slot");
    queue.finish("adult-a", "slot", "image-a");
    expect(queue.image("adult-a")).toBe("image-a");
    expect(queue.active?.owner).toBe("next");
  });
  it("cancels invisible work and rejects its late result", () => {
    const queue = new PortraitQueue();
    const cancel = queue.request("a", "old"); queue.request("b", "new"); cancel();
    queue.finish("a", "old", "late");
    expect(queue.image("a")).toBeUndefined(); expect(queue.active?.key).toBe("b");
  });
  it("evicts old snapshots to keep memory bounded", () => {
    const queue = new PortraitQueue(1);
    queue.request("a", "first"); queue.finish("a", "first", "a-image");
    queue.request("b", "second"); queue.finish("b", "second", "b-image");
    expect(queue.image("a")).toBeUndefined(); expect(queue.image("b")).toBe("b-image");
  });
});
