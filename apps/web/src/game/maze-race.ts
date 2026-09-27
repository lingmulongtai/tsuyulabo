import type { components } from "@/lib/api/schema";

export type MazeToken = components["schemas"]["MazeToken"];
export type MazeGeometry = components["schemas"]["MazeGeometry"];
export const RACE_CUES = [
  { id: "banana", label: "バナナ" },
  { id: "apple_vinegar", label: "りんご酢" },
  { id: "yeast", label: "酵母" },
  { id: "grape", label: "ぶどう" },
  { id: "blue_light", label: "青い光" },
] as const;

export function placeToken(maze: MazeGeometry, tokens: MazeToken[], token: MazeToken): { tokens: MazeToken[]; message: string } {
  if (maze.grid[token.y]?.[token.x] !== ".") return { tokens, message: "壁には置けません。通路を選んでください。" };
  const existing = tokens.find(item => item.x === token.x && item.y === token.y);
  if (existing) return { tokens: tokens.filter(item => item !== existing), message: "合図を取り除きました。" };
  if (tokens.length === 3) return { tokens, message: "合図は3つまでです。置いた合図をタップすると取り除けます。" };
  return { tokens: [...tokens, token], message: "合図を置きました。" };
}

export function raceScore(result: { reached: boolean; steps: number; distance_left: number }): string {
  return result.reached ? `${result.steps}歩でゴール！` : `ゴールまであと${result.distance_left}マス`;
}
