"use client";
import { useRef, useState } from "react";
import { Button, Card } from "../ui/primitives";
import { CareVial } from "../vivarium/CareVial";
import { wipeMask, wipePreview, type WipeStamp, type WipeSubmission } from "@/game/puzzles/wiping";
import type { CleaningParams } from "@/game/puzzles/types";
import { useGameTimer } from "./useGameTimer";

export function CleaningGame({ onFinish }: { params: CleaningParams; onFinish: (value: WipeSubmission) => void }) {
  const timer = useGameTimer(10_000);
  const stamps = useRef<WipeStamp[]>([]);
  const [wiped, setWiped] = useState<WipeStamp[]>([]);
  const finished = useRef(false);
  const preview = wipePreview(wiped, timer.elapsed), mask = wipeMask(wiped);
  const stamp = (u: number, v: number) => {
    const t = timer.now();
    if (!timer.running || t > 10_000 || stamps.current.length >= 800 || t - (stamps.current.at(-1)?.t ?? -100) < 12) return;
    stamps.current.push({ u, v, t }); setWiped([...stamps.current]);
  };
  const finish = () => {
    if (finished.current || stamps.current.length < 2) return;
    finished.current = true; timer.stop();
    onFinish({ strokes: [...stamps.current], elapsed_ms: Math.min(10_000, timer.now()) });
  };
  return <Card className="space-y-3 p-3">
    <p className="text-sm text-muted">指でガラスを拭いて、曇りと汚れを落としましょう。広く、ていねいに。10秒以内です。</p>
    <div style={{ touchAction: "none" }}><CareVial onGlassStroke={timer.running ? stamp : undefined} wiped={wiped} /></div>
    <p role="status" className="text-sm">拭いたところ {Math.round(preview.coverage * 100)}% ・ 残り {((10_000 - timer.elapsed) / 1000).toFixed(1)}秒</p>
    <details><summary className="min-h-11 text-xs text-muted">静止画・キーボードで拭く</summary>
      <div className="grid grid-cols-6 overflow-hidden rounded-lg" role="group" aria-label="ガラスの清掃面">
        {Array.from({ length: 54 }, (_, i) => <button key={i} aria-label={`ガラス ${Math.floor(i / 6) + 1}行${i % 6 + 1}列`} disabled={!timer.running}
          className="h-8 border border-white/10" style={{ background: mask[Math.floor(i / 6) * 24 + i % 6 * 2] ? "#d8dccb" : "#818566" }}
          onClick={() => stamp((i % 6 + 0.5) / 6, (Math.floor(i / 6) + 0.5) / 9)} />)}
      </div>
    </details>
    {!timer.running && !timer.expired && <Button block onClick={() => { stamps.current = []; setWiped([]); finished.current = false; timer.start(); }}>スタート</Button>}
    {(timer.running || timer.expired) && <Button block disabled={wiped.length < 2} onClick={finish}>拭き終わる</Button>}
    {timer.expired && <p className="text-xs text-muted">拭いた範囲を保存できます。</p>}
  </Card>;
}
