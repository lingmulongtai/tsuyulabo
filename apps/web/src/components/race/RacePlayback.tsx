"use client";

import { useEffect, useState } from "react";
import type { TsuyuProps } from "@/components/art/Tsuyu";
import { Button, Card } from "@/components/ui/primitives";
import { raceScore } from "@/game/maze-race";
import type { RaceReplay } from "@/lib/api/hooks-race";
import { MazeBoard } from "./MazeBoard";

export function RacePlayback({ replay, appearance }: { replay: RaceReplay; appearance?: Pick<TsuyuProps, "strain" | "sex"> }) {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(2);
  const result = replay.result;
  const last = (result?.frames.length ?? 1) - 1;
  useEffect(() => {
    if (!playing || step >= last) return;
    const timer = setTimeout(() => setStep(value => Math.min(last, value + 1)), 400 / speed);
    return () => clearTimeout(timer);
  }, [playing, step, last, speed]);
  if (!result) return <Card className="p-5"><p role="status">{replay.entry.status === "failed" ? "走行の計算に失敗しました。もう一度エントリーしてください。" : "ツユの脳がコースを走っています…"}</p></Card>;
  return <Card className="space-y-4 p-4">
    <div className="flex items-center justify-between"><h2 className="font-kiwi text-lg">走りを振り返る</h2><b className="font-mono text-ai">{step} / {last} 歩</b></div>
    <MazeBoard maze={replay.maze} tokens={replay.entry.placements} frame={result.frames[step]} appearance={appearance} />
    <div className="flex flex-wrap items-center gap-3">
      <Button tone="ai" size="sm" onClick={() => { if (step === last) setStep(0); setPlaying(!playing || step === last); }}>{playing && step < last ? "一時停止" : "再生"}</Button>
      <Button tone="plain" size="sm" onClick={() => { setStep(0); setPlaying(false); }}>最初へ</Button>
      <label className="text-sm">速さ <select className="rounded-lg border border-line bg-bg p-2" value={speed} onChange={event => setSpeed(Number(event.target.value))}>
        {[1, 2, 4, 8].map(value => <option key={value} value={value}>{value}倍</option>)}
      </select></label>
    </div>
    <label className="block text-xs text-muted">見たい歩数へ<input aria-label="リプレイの歩数" className="mt-2 w-full accent-ai" type="range" min={0} max={last} value={step} onChange={event => { setPlaying(false); setStep(Number(event.target.value)); }} /></label>
    <p className="text-center font-bold text-leaf">{raceScore(result)}</p>
  </Card>;
}
