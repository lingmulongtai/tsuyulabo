"use client";

import { Tsuyu } from "@/components/art/Tsuyu";
import type { TsuyuProps } from "@/components/art/Tsuyu";
import { RACE_CUES, type MazeGeometry, type MazeToken } from "@/game/maze-race";
import type { components } from "@/lib/api/schema";

export function MazeBoard({ maze, tokens, onCell, frame, appearance }: {
  maze: MazeGeometry; tokens: MazeToken[]; onCell?: (x: number, y: number) => void;
  frame?: components["schemas"]["MazeFrame"]; appearance?: Pick<TsuyuProps, "strain" | "sex">;
}) {
  return <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-2xl border-4 border-line bg-line" aria-label="9×9の迷路">
    <div className="grid grid-cols-9 gap-px">
      {maze.grid.flatMap((row, y) => [...row].map((cell, x) => {
        const token = tokens.find(item => item.x === x && item.y === y);
        const cue = RACE_CUES.find(item => item.id === token?.cue);
        const start = x === maze.start[0] && y === maze.start[1];
        const goal = x === maze.goal[0] && y === maze.goal[1];
        const label = `${x + 1}列${y + 1}行${start ? "・スタート" : goal ? "・ゴール" : ""}${cue ? `・${cue.label}` : ""}`;
        const className = `relative flex aspect-square items-center justify-center text-base sm:text-xl ${cell === "#" ? "bg-ink/75" : goal ? "bg-tint-leaf text-leaf" : "bg-surface-2"}`;
        return onCell && cell !== "#" ? <button key={`${x},${y}`} className={`${className} focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-ai`} aria-label={label} aria-pressed={Boolean(token)} onClick={() => onCell(x, y)}>
          {cue?.icon ?? (start ? "出" : goal ? "旗" : "")}
        </button> : <div key={`${x},${y}`} className={className} aria-label={cell === "#" ? "壁" : label}>{cue?.icon ?? (start ? "出" : goal ? "旗" : "")}</div>;
      }))}
    </div>
    {frame && <div className="pointer-events-none absolute h-[11.111%] w-[11.111%] transition-[left,top] duration-100 motion-reduce:transition-none" style={{ left: `${frame.x / 9 * 100}%`, top: `${frame.y / 9 * 100}%` }}>
      <div style={{ transform: `rotate(${frame.heading * 90}deg)` }}><Tsuyu {...appearance} label="走っているツユ" className="h-full w-full drop-shadow" /></div>
    </div>}
  </div>;
}
