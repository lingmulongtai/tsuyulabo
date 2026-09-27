"use client";
import { useRef, useState } from "react";
import { FlyArt } from "../art/FlyArt";
import { Button, Card } from "../ui/primitives";
import { markerPosition, gradeTap } from "@/game/puzzles/cleaning";
import type { CleaningParams, CleaningSubmission, Grade } from "@/game/puzzles/types";
import * as Sound from "@/game/audio/sound";
import { buzz } from "@/game/audio/haptics";
import { useGameTimer } from "./useGameTimer";

export function CleaningGame({ params, onFinish }: { params: CleaningParams; onFinish: (value: CleaningSubmission) => void }) {
  const timer = useGameTimer(10_000);
  const taps = useRef<number[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const x = markerPosition(params, timer.elapsed);
  const tap = () => {
    const t = timer.now();
    if (!timer.running || t > 10_000 || taps.current.length >= params.taps || t <= (taps.current.at(-1) ?? -1)) return;
    taps.current.push(t);
    const grade = gradeTap(params, t);
    setGrades(previous => [...previous, grade]);
    if (grade === "perfect") { Sound.perfect(); buzz([15, 20, 15]); }
    else if (grade === "good") { Sound.tap(); buzz(15); }
    else { Sound.bad(); buzz(5); }
    if (taps.current.length === params.taps) {
      timer.stop();
      onFinish({ taps: [...taps.current], elapsed_ms: t });
    }
  };
  return <Card className="space-y-5 p-5 text-center">
    <p className="text-sm text-muted">まんなかの緑をねらって、びんを３回トントン！</p>
    <button onClick={tap} disabled={!timer.running} aria-label="びんをたたく" className="relative mx-auto block h-56 w-44 rounded-b-[60px] border-4 border-[#9dbbb4] bg-tint-leaf touch-manipulation" style={{ transform: `rotate(${timer.running ? Math.sin(timer.elapsed / 75) * 2 : 0}deg)` }}>
      <span className="absolute -inset-x-3 -top-4 h-8 rounded-xl border-2 border-[#c9bfa9] bg-[#e9e1cf]" />
      <FlyArt stage="larva2" className="absolute bottom-0 w-full" />
      <span className="absolute left-4 top-8 h-24 w-3 rounded-full bg-white/60" />
    </button>
    <div className="relative h-9 overflow-hidden rounded-full bg-line-soft" aria-label="タイミングゾーン">
      <div className="absolute inset-y-0 bg-tint-leaf" style={{ left: `${(params.zone.center - params.zone.good) * 100}%`, width: `${params.zone.good * 200}%` }} />
      <div className="absolute inset-y-0 bg-leaf" style={{ left: `${(params.zone.center - params.zone.perfect) * 100}%`, width: `${params.zone.perfect * 200}%` }} />
      <div className="absolute inset-y-1 w-2 -translate-x-1/2 rounded-full bg-eye shadow" style={{ left: `${x * 100}%` }} />
    </div>
    <div aria-live="polite" className="flex h-10 justify-center gap-2">{grades.map((grade, i) => <span key={i} className={`pop-in rounded-xl px-2 py-1 font-mono font-bold ${grade === "miss" ? "bg-tint-eye text-eye" : "bg-tint-leaf text-leaf"}`}>{grade.toUpperCase()}</span>)}</div>
    {timer.running ? <Button block size="lg" tone="leaf" onClick={tap}>トン！ あと{params.taps - grades.length}回</Button> :
      <Button block size="lg" tone="leaf" onClick={() => { Sound.init(); taps.current = []; setGrades([]); timer.start(); }}>{timer.expired ? "もう一度スタート" : "スタート"}</Button>}
    <p className="text-xs text-muted" role="status">{timer.expired ? "時間切れです。もう一度ためしてみよう。" : `残り ${((10_000 - timer.elapsed) / 1000).toFixed(1)} 秒`}</p>
  </Card>;
}
