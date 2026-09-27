"use client";

import { useEffect, useMemo, useState } from "react";
import { TruthBadge } from "../ui/primitives";
import type { Sex, Strain } from "./palette";
import { Tsuyu } from "./Tsuyu";

export type Behavior = "rest" | "walk" | "turn_left" | "turn_right" | "feed" | "escape" | "groom" | "approach" | "avoid";

export const BEHAVIOR_LABELS: Record<Behavior, string> = {
  rest: "じっとしている",
  walk: "歩く",
  turn_left: "左に曲がる",
  turn_right: "右に曲がる",
  feed: "食べる",
  escape: "逃げる",
  groom: "身づくろい",
  approach: "近づく",
  avoid: "離れる",
};

function pickWeighted(probs: Partial<Record<Behavior, number>>, r: number): Behavior {
  const entries = Object.entries(probs) as Array<[Behavior, number]>;
  const total = entries.reduce((s, [, p]) => s + Math.max(0, p), 0) || 1;
  let x = r * total;
  for (const [b, p] of entries) {
    x -= Math.max(0, p);
    if (x < 0) return b;
  }
  return entries[0]?.[0] ?? "rest";
}

/**
 * The adult fly moving according to the behaviour decoder's output (GET /v1/flies/{id}/behavior). Every few
 * seconds it samples a behaviour from the probabilities, so a 70 % groom fly mostly grooms but not always.
 */
export function BehaviorFly({
  probs,
  strain,
  sex,
  showBars = true,
}: {
  probs: Partial<Record<Behavior, number>>;
  strain?: Strain;
  sex?: Sex;
  showBars?: boolean;
}) {
  const top = useMemo(() => pickWeighted(probs, 0), [probs]);
  const [current, setCurrent] = useState<Behavior>(top);

  useEffect(() => {
    const id = setInterval(() => setCurrent(pickWeighted(probs, Math.random())), 4200);
    return () => clearInterval(id);
  }, [probs]);

  const pose = current === "groom" ? "groom" : current === "feed" ? "feed" : "idle";
  const sorted = (Object.entries(probs) as Array<[Behavior, number]>).sort((a, b) => b[1] - a[1]).slice(0, 4);

  return (
    <div className="flex flex-col gap-3">
      <div className="relative aspect-[1.4/1] w-full overflow-hidden rounded-[28px] bg-[radial-gradient(circle_at_50%_40%,#ffffff,#e4f4ef_50%,var(--stage-glow))]">
        {current === "escape" && (
          <div className="absolute -top-6 left-1/2 size-40 -translate-x-1/2 rounded-full bg-[#1e2c29]/25 blur-md motion-safe:animate-pulse" aria-hidden />
        )}
        {(current === "approach" || current === "avoid") && (
          <div className="absolute right-[8%] top-[38%] size-16 rounded-full bg-[radial-gradient(circle,rgba(242,201,76,.8),transparent_70%)] motion-safe:animate-pulse" aria-hidden />
        )}
        {current === "feed" && <div className="absolute bottom-[12%] left-1/2 h-3 w-24 -translate-x-1/2 rounded-full bg-[#f6da82]" aria-hidden />}
        <div className="absolute inset-x-0 bottom-[6%] mx-auto w-[46%]">
          <div key={current} className={`bh-${current}`}>
            <Tsuyu strain={strain} sex={sex} animated pose={pose} className="block h-auto w-full" />
          </div>
        </div>
        <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-white/85 px-3 py-0.5 text-sm font-bold text-[#1e2c29]">
          いま：{BEHAVIOR_LABELS[current]}
        </div>
      </div>

      {showBars && (
        <div className="rounded-2xl border border-line-soft bg-surface-2 px-4 py-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-muted">
            脳のモデルが選んだ行動 <TruthBadge kind="model" />
          </div>
          <ul className="space-y-1">
            {sorted.map(([b, p]) => (
              <li key={b} className="flex items-center gap-2 text-xs">
                <span className="w-24 shrink-0 whitespace-nowrap">{BEHAVIOR_LABELS[b]}</span>
                <span className="h-2 flex-1 overflow-hidden rounded-full bg-line-soft">
                  <span className="block h-full rounded-full bg-leaf" style={{ width: `${Math.round(p * 100)}%` }} />
                </span>
                <span className="w-9 text-right font-mono tabular">{Math.round(p * 100)}%</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
