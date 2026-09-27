"use client";
import { useRef } from "react";
import { Button, Card } from "../ui/primitives";
import { needleTemp, scoreTemperature } from "@/game/puzzles/temperature";
import type { TemperatureParams, TemperatureSubmission } from "@/game/puzzles/types";
import * as Sound from "@/game/audio/sound";
import { buzz } from "@/game/audio/haptics";
import { useGameTimer } from "./useGameTimer";

export function TemperatureGame({ params, onFinish }: { params: TemperatureParams; onFinish: (value: TemperatureSubmission) => void }) {
  const timer = useGameTimer(600_000);
  const finished = useRef(false);
  const temp = needleTemp(params, timer.elapsed);
  const stop = () => {
    if (!timer.running || finished.current) return;
    const t = timer.now();
    if (t > 600_000) return;
    finished.current = true;
    timer.stop();
    const grade = scoreTemperature(params, t).grade;
    if (grade === "perfect") Sound.perfect(); else if (grade === "good") Sound.tap(); else Sound.bad();
    buzz(20);
    onFinish({ stop_ms: t, elapsed_ms: t });
  };
  return <Card className="space-y-5 p-6 text-center">
    <p className="text-sm text-muted">ツユが過ごしやすい、25℃をねらおう。</p>
    <div className="relative mx-auto size-64 rounded-full border-8 border-line bg-bg shadow-inner">
      <span className="absolute inset-x-0 top-4 font-mono font-bold text-leaf">25℃</span>
      <span className="absolute bottom-12 left-4 text-sm text-muted">ひんやり</span><span className="absolute bottom-12 right-4 text-sm text-muted">ぽかぽか</span>
      <div className="absolute bottom-1/2 left-1/2 h-20 w-2 origin-bottom -translate-x-1/2 rounded-full bg-eye" style={{ transform: `translateX(-50%) rotate(${(temp - 25) * 10}deg)` }} />
      <div className="absolute left-1/2 top-1/2 size-5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink" />
      <div className="absolute inset-x-0 bottom-3 font-mono text-2xl tabular">{temp.toFixed(1)}℃</div>
    </div>
    {timer.running ? <Button block size="lg" onClick={stop}>ここでストップ！</Button> :
      <Button block size="lg" tone="banana" onClick={() => { Sound.init(); finished.current = false; timer.start(); }}>スタート</Button>}
    {timer.expired && <p role="status" className="text-sm text-muted">時間が経ちました。ホームから問題を開き直してください。</p>}
  </Card>;
}
