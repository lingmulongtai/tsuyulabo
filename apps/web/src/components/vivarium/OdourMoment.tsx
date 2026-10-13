"use client";
import { useEffect, useRef } from "react";
import { useExperiment, useJob } from "@/lib/api/hooks";
import { odourBehaviour } from "@/game/vial";
import { CUE_INFO } from "@/game/labels";
import type { Cue } from "@/game/puzzles/types";
import type { Behaviour } from "./types";
import { ErrorCard } from "../ui/QueryState";
import { usePageVisible } from "./lifecycle";
import { MomentClock } from "./moment-clock";

export function OdourMoment({ flyId, cue, onBehaviour, disabled = false, paused = false }: { flyId: string; cue: Cue; disabled?: boolean; paused?: boolean; onBehaviour: (value: Behaviour | undefined) => void }) {
  const experiment = useExperiment();
  const job = useJob(experiment.data?.job_id);
  const action = job.data?.status === "succeeded" ? odourBehaviour(job.data.result?.result) : undefined;
  const visible = usePageVisible();
  const clock = useRef(new MomentClock(8000));
  const observation = experiment.data?.job_id;
  useEffect(() => {
    if (!action) return;
    clock.current = new MomentClock(8000);
    onBehaviour(action);
    return () => onBehaviour(undefined);
  }, [action, observation, onBehaviour]);
  useEffect(() => {
    if (!action || paused || !visible) return;
    const current = clock.current;
    current.resume(performance.now());
    const timer = setInterval(() => {
      if (current.advance(performance.now())) { clearInterval(timer); onBehaviour(undefined); }
    }, 100);
    return () => { clearInterval(timer); current.suspend(performance.now()); };
  }, [action, observation, paused, visible, onBehaviour]);
  const busy = experiment.isPending || (Boolean(experiment.data) && !job.error && !["succeeded", "failed"].includes(job.data?.status ?? "pending"));
  return <div className="space-y-2">
    <button className="glass-panel min-h-11 rounded-lg px-3 py-2 text-sm" disabled={disabled || busy || paused} onClick={() => experiment.mutate({ fly_id: flyId, kind: "odor_choice", cue, trials: 1 })}>{CUE_INFO[cue].name}を置く</button>
    <p role="status" className="text-sm">{disabled ? "しつけを覚えているところです。" : busy ? "匂いに気づくのを待っています…" : action === "approach" ? `${CUE_INFO[cue].name}に寄っていった` : action === "avoid" ? `${CUE_INFO[cue].name}から離れていった` : action === "rest" ? "その場で、じっとしていた" : "この子の好き・苦手を、動きで見てみよう。"}</p>
    {(experiment.error || job.error) && <ErrorCard error={experiment.error ?? job.error} />}
    {job.data?.status === "failed" && <p className="text-sm">今は様子を読み取れませんでした。もう一度匂いを置けます。</p>}
  </div>;
}
