"use client";
import { useEffect, useRef, useState } from "react";
import type { TierIndex } from "@/game/expectation";
import type { VialState } from "@/game/vial";
import { habitat, sitePosition } from "@/game/vial";
import { Vivarium, type Phenotype } from "../vivarium/Vivarium";
import { useCalmMotion, usePageVisible } from "../vivarium/lifecycle";
import { STRAIN_LABELS, type Sex, type Strain } from "../art/palette";
import { Button } from "../ui/primitives";
import { RANK_LABELS, TIER_NAMES, traitName } from "./traits";

export interface EclosionResult {
  tier: TierIndex;
  omen_sequence: number[];
  adult: { id?: string; name: string; strain: Strain; sex: Sex; stars: number; traits: string[]; phenotypes?: Phenotype[] };
  vial?: VialState;
  evaluation?: { rank: keyof typeof RANK_LABELS };
}

export function EclosionStage({ result, onStart, onDone, doneLabel = "飼育室へ", vial }: { result: EclosionResult | null; onStart?: () => void; onDone: () => void; doneLabel?: string; vial?: VialState | null }) {
  const [started, setStarted] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [paused, setPaused] = useState(false);
  const calm = useCalmMotion(), visible = usePageVisible();
  const last = useRef<number | null>(null);
  const duration = calm ? 700 : 7000;
  const progress = Math.min(1, elapsed / duration);
  const completed = progress >= 1;
  useEffect(() => {
    if (!result || !started || paused || !visible || completed) { last.current = null; return; }
    const timer = setInterval(() => {
      const now = performance.now();
      const dt = last.current === null ? 0 : Math.min(250, now - last.current);
      last.current = now;
      setElapsed(value => value + dt);
    }, 100);
    return () => { clearInterval(timer); last.current = null; };
  }, [result, started, paused, visible, completed, duration]);
  const saved = result?.vial ?? vial;
  const ready = Boolean(result && progress >= 1);
  const emerging = Boolean(result && started && progress > 0.15);
  return <div className="relative overflow-hidden rounded-xl" style={{ height: "max(620px, 82svh)" }} data-eclosion-vial>
    <Vivarium stage={emerging ? "adult" : "pupa"} seed={result?.adult.id ?? "eclosion"} environment={{ ...habitat(saved), pupaAge: 1 }}
      sex={result?.adult.sex} traits={result?.adult.phenotypes ?? (result ? [result.adult.strain] : undefined)}
      pupationPosition={sitePosition(saved?.pupation_position)} framing="close" behaviour="rest" paused={paused || !started || !result || completed}
      eclosionProgress={emerging ? progress : undefined} />
    {!started && <div className="glass-panel absolute inset-x-4 bottom-4 space-y-3 rounded-lg p-4 text-center">
      <p className="text-sm">殻の中で、翅を広げる準備が進んでいます。</p>
      <Button onClick={() => { setStarted(true); onStart?.(); }}>羽化を見届ける</Button>
    </div>}
    {started && !ready && <>
      <div className="absolute inset-x-3 top-3 flex justify-between gap-2">
        <button className="glass-panel min-h-11 rounded-lg px-3 text-xs" onClick={() => setPaused(value => !value)}>{paused ? "再開" : "一時停止"}</button>
        <button className="glass-panel min-h-11 rounded-lg px-3 text-xs" disabled={!result} onClick={() => setElapsed(duration)}>スキップ</button>
      </div>
      <p role="status" className="glass-panel absolute inset-x-4 bottom-4 rounded-lg p-3 text-center text-sm">{!result ? "羽化を待っています…" : progress < 0.3 ? "殻を押し開けて、外へ。" : progress < 0.75 ? "小さな翅が、ゆっくり広がる。" : "翅が乾いて、羽ばたく準備が整います。"}</p>
    </>}
    {ready && result && <div className="glass-panel absolute inset-x-4 bottom-4 space-y-2 rounded-lg p-4 text-center" data-eclosion-evaluation>
      <h2 className="text-xl">{TIER_NAMES[result.tier]}</h2>
      {result.evaluation && <p className="text-sm">育ちの評価 ・ {RANK_LABELS[result.evaluation.rank]}</p>}
      <p>{result.adult.name} ・ {result.adult.sex === "m" ? "オス" : "メス"} ・ {STRAIN_LABELS[result.adult.strain].name}</p>
      <p className="text-xs text-muted">{result.adult.traits.map(traitName).join(" ・ ")}</p>
      <details className="text-xs text-muted"><summary>この子の素質</summary>{"★".repeat(result.adult.stars)}</details>
      <Button onClick={onDone}>{doneLabel}</Button>
    </div>}
  </div>;
}
