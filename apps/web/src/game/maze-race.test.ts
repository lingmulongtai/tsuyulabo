import { describe, expect, it } from "vitest";
import { placeToken, raceScore, type MazeGeometry, type MazeToken } from "./maze-race";

const maze: MazeGeometry = { grid: ["#####", "#...#", "#...#"], start: [1, 1], goal: [3, 2] };
const token: MazeToken = { x: 1, y: 1, cue: "banana" };

describe("maze editor", () => {
  it("rejects walls, bounds and a fourth token without mutating input", () => {
    const tokens = [token, { ...token, x: 2 }, { ...token, x: 3 }];
    expect(placeToken(maze, tokens, { ...token, y: 2 }).tokens).toBe(tokens);
    expect(placeToken(maze, tokens, { ...token, x: 0 }).tokens).toBe(tokens);
    expect(placeToken(maze, tokens, { ...token, y: 9 }).tokens).toBe(tokens);
    expect(tokens).toHaveLength(3);
  });
  it("allows repeated cues and removes an occupied cell even when full", () => {
    const second = placeToken(maze, [token], { ...token, x: 2 }).tokens;
    expect(second).toHaveLength(2);
    expect(placeToken(maze, second, { ...token, cue: "grape" }).tokens).toEqual([{ ...token, x: 2 }]);
  });
  it("distinguishes finishing from distance remaining", () => {
    expect(raceScore({ reached: true, steps: 25, distance_left: 0 })).toBe("25歩でゴール！");
    expect(raceScore({ reached: false, steps: 400, distance_left: 3 })).toBe("ゴールまであと3マス");
  });
});
