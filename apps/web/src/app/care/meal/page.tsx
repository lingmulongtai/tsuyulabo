"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { CareFrame, ResultSheet } from "@/components/games/CareFrame";
import type { MealFinish } from "@/components/games/MealGame";
import { AppShell } from "@/components/shell/AppShell";
import { practiceMeal } from "@/game/practice";

// Practice params are random, so the board is rendered on the client only (no SSR mismatch).
const MealGame = dynamic(() => import("@/components/games/MealGame").then((m) => m.MealGame), { ssr: false });

interface Outcome {
  finish: MealFinish;
  great: boolean;
}

export default function MealPage() {
  const [params] = useState(() => practiceMeal(Math.floor(Math.random() * 1e9)));
  const [outcome, setOutcome] = useState<Outcome | null>(null);

  const onFinish = (finish: MealFinish) => {
    // Practice mode: the server rolls this in real play (docs/specs/puzzles.md §1).
    const p = Math.min(0.35, 0.04 + finish.score / 12000);
    setOutcome({ finish, great: Math.random() < p });
  };

  return (
    <AppShell hideTabs>
      <CareFrame title="ごはんづくり" subtitle="30秒で、材料ブロックの列をそろえて消そう">
        <MealGame params={params} onFinish={onFinish} />
      </CareFrame>
      {outcome && (
        <ResultSheet
          heading={`おいしさ ${outcome.finish.score.toLocaleString("ja-JP")}`}
          great={outcome.great}
          lines={[
            { label: "おなか", value: outcome.great ? "+60" : "+40", tone: "banana" },
            { label: "成長ポイント", value: `+${((outcome.finish.score / 100) * (outcome.great ? 2 : 1)).toFixed(1)}`, tone: "leaf" },
            { label: "発表会のポイント", value: `+${(outcome.finish.score + (outcome.great ? 1000 : 0)).toLocaleString("ja-JP")}`, tone: "eye" },
          ]}
          primary={{ label: "ホームへ", href: "/" }}
        />
      )}
    </AppShell>
  );
}
