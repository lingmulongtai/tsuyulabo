"use client";

import { useState } from "react";
import { BEHAVIOR_LABELS, BehaviorFly, type Behavior } from "@/components/art/BehaviorFly";
import { CareFrame } from "@/components/games/CareFrame";
import { AppShell } from "@/components/shell/AppShell";

/** Showcase of every behaviour the decoder can output (useful for checking the animations). */
export default function BehaviorLabPage() {
  const [focus, setFocus] = useState<Behavior>("groom");
  const probs: Partial<Record<Behavior, number>> = { [focus]: 0.72, rest: 0.14, walk: 0.08, feed: 0.06 };
  return (
    <AppShell hideTabs>
      <CareFrame title="行動のようす" subtitle="神経活動から行動を当てるデコーダーの出力で動く">
        <BehaviorFly probs={probs} />
        <div className="grid grid-cols-3 gap-2">
          {(Object.keys(BEHAVIOR_LABELS) as Behavior[]).map((b) => (
            <button
              key={b}
              type="button"
              onClick={() => setFocus(b)}
              aria-pressed={focus === b}
              className={`whitespace-nowrap rounded-2xl border-2 bg-surface-2 py-2 text-[0.7rem] font-bold ${focus === b ? "border-leaf" : "border-line-soft"}`}
            >
              {BEHAVIOR_LABELS[b]}
            </button>
          ))}
        </div>
      </CareFrame>
    </AppShell>
  );
}
