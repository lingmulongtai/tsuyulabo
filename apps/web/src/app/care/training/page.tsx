"use client";

import { useState } from "react";
import { CareFrame, ResultSheet } from "@/components/games/CareFrame";
import { TeachPicker } from "@/components/games/TeachPicker";
import { TrainingGame, type TrainingFinish } from "@/components/games/TrainingGame";
import { AppShell } from "@/components/shell/AppShell";
import { CUE_INFO, VALENCE_INFO } from "@/game/labels";
import { practiceTraining } from "@/game/practice";
import type { TrainingParams } from "@/game/puzzles/types";

interface Outcome {
  finish: TrainingFinish;
  hirameki: boolean;
}

export default function TrainingPage() {
  const [params, setParams] = useState<TrainingParams | null>(null);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [round, setRound] = useState(0);

  const onFinish = (finish: TrainingFinish) => {
    // Practice mode: the server rolls ひらめき and runs the brain model in real play.
    const chance = finish.stars === 3 ? 0.15 : 0.1;
    setOutcome({ finish, hirameki: Math.random() < chance });
  };

  const strength = outcome ? outcome.finish.stars * 0.12 * (outcome.hirameki ? 2 : 1) : 0;

  return (
    <AppShell hideTabs>
      <CareFrame title="しつけ" subtitle="回路パズルで、好き・苦手を教えよう">
        {params ? (
          <TrainingGame key={round} params={params} onFinish={onFinish} />
        ) : (
          <TeachPicker onPick={(cue, valence) => setParams(practiceTraining(round, cue, valence))} />
        )}
      </CareFrame>
      {outcome && params && (
        <ResultSheet
          heading="覚えた！"
          great={outcome.hirameki}
          greatLabel="ひらめき！"
          lines={[
            { label: "教えたこと", value: `${CUE_INFO[params.cue].short}${VALENCE_INFO[params.valence].effect}`, tone: "ai" },
            { label: "★", value: "★".repeat(outcome.finish.stars), tone: "banana" },
            { label: "つながりの変化", value: `${params.valence === "reward" ? "+" : "−"}${Math.round(strength * 100)}%`, tone: "leaf" },
          ]}
          primary={{
            label: "もう一回",
            onClick: () => {
              setOutcome(null);
              setParams(null);
              setRound((r) => r + 1);
            },
          }}
        >
          <p className="mt-2 text-xs text-muted">キノコ体のつながりが変わりました（ゲーム内のモデル）。</p>
        </ResultSheet>
      )}
    </AppShell>
  );
}
