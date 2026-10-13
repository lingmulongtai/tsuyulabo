"use client";
import { useRef, useState } from "react";
import { Button, Card } from "../ui/primitives";
import { CareVial } from "../vivarium/CareVial";
import { useHome } from "@/lib/api/hooks";
import { habitat } from "@/game/vial";
import { needleTemp, scoreTemperature } from "@/game/puzzles/temperature";
import type { TemperatureParams, TemperatureSubmission } from "@/game/puzzles/types";
import * as Sound from "@/game/audio/sound";
import { buzz } from "@/game/audio/haptics";
import { useGameTimer } from "./useGameTimer";

const MIN_C = 17;
const MAX_C = 33;
const R = 110;
const CX = 130;
const CY = 130;

/** Temperature → angle on the half dial (−90° = cold end, +90° = hot end). */
function angleOf(temp: number) {
  const k = (Math.min(MAX_C, Math.max(MIN_C, temp)) - MIN_C) / (MAX_C - MIN_C);
  return -90 + k * 180;
}

function polar(angleDeg: number, r: number) {
  const a = ((angleDeg - 90) * Math.PI) / 180;
  return { x: CX + r * Math.cos(a), y: CY + r * Math.sin(a) };
}

function arc(fromC: number, toC: number, r: number) {
  const a = polar(angleOf(fromC), r);
  const b = polar(angleOf(toC), r);
  const large = angleOf(toC) - angleOf(fromC) > 180 ? 1 : 0;
  return `M ${a.x} ${a.y} A ${r} ${r} 0 ${large} 1 ${b.x} ${b.y}`;
}

function readoutColor(temp: number) {
  const d = Math.abs(temp - 25);
  return d <= 0.5 ? "#1f8579" : d <= 2 ? "#c98a12" : "#d7263d";
}

/**
 * 温度あわせ — stop the swinging needle close to 25 ℃. Real flies develop fastest and most smoothly around 25 ℃;
 * the score comes from how far the needle is from it when stopped.
 */
export function TemperatureGame({ params, onFinish, stage = "egg" }: { params: TemperatureParams; onFinish: (value: TemperatureSubmission) => void; stage?: "egg" | "pupa" }) {
  const home = useHome();
  const [humidity, setHumidity] = useState<number | null>(null);
  const moisture = humidity ?? home.data?.vial?.humidity ?? 0.65;
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
    if (grade === "perfect") Sound.perfect();
    else if (grade === "good") Sound.tap();
    else Sound.bad();
    buzz(20);
    onFinish({ stop_ms: t, elapsed_ms: t, humidity: moisture });
  };
  const needle = polar(angleOf(temp), R - 14);

  return (
    <Card className="space-y-4 p-5 text-center">
      <p className="text-sm text-muted">ダイヤルに触れて、針を25℃で止めましょう。湿度を回すと、ガラスの水滴が変わります。</p>
      <CareVial stage={home.data?.fly?.stage ?? stage} environment={{ ...habitat(home.data?.vial), temperature: temp, humidity: moisture }}>
      <div className="glass-panel absolute right-3 top-3 w-[min(58%,220px)] rounded-lg p-2">
      <div className="relative mx-auto w-full max-w-[300px] touch-none" onPointerDown={event => { event.currentTarget.setPointerCapture(event.pointerId); }} onPointerUp={stop}>
        <svg viewBox="-24 -26 308 176" className="w-full" aria-hidden>
          <defs>
            <linearGradient id="thermoArc" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#5ec8f2" />
              <stop offset=".5" stopColor="#7ee0a1" />
              <stop offset="1" stopColor="#ff6b6b" />
            </linearGradient>
          </defs>
          <path d={arc(MIN_C, MAX_C, R)} stroke="var(--line-soft)" strokeWidth={26} fill="none" strokeLinecap="round" />
          <path d={arc(MIN_C, MAX_C, R)} stroke="url(#thermoArc)" strokeWidth={18} fill="none" strokeLinecap="round" opacity={0.85} />
          <path d={arc(23, 27, R)} stroke="#fff" strokeWidth={22} fill="none" opacity={0.35} />
          <path d={arc(24.5, 25.5, R)} stroke="#1f8579" strokeWidth={26} fill="none" />
          {[18, 21, 25, 29, 32].map((c) => {
            const p = polar(angleOf(c), R + 22);
            return (
              <text key={c} x={p.x} y={p.y + 4} textAnchor="middle" fontSize={11} fill="var(--muted)" fontFamily="var(--font-mono)">
                {c}
              </text>
            );
          })}
          <line x1={CX} y1={CY} x2={needle.x} y2={needle.y} stroke="var(--ink)" strokeWidth={5} strokeLinecap="round" />
          <circle cx={CX} cy={CY} r={9} fill="var(--ink)" />
          <circle cx={CX} cy={CY} r={3.5} fill="var(--surface-2)" />
        </svg>
      </div>
      <label className="block text-sm">湿度 {Math.round(moisture * 100)}%
        <input type="range" aria-label="湿度ダイヤル" min={20} max={95} step={1} value={Math.round(moisture * 100)} onChange={event => setHumidity(Number(event.target.value) / 100)} className="block w-full min-h-11 accent-amber-700" />
      </label>
      <div className="font-mono text-2xl tabular" style={{ color: readoutColor(temp) }}>
        {temp.toFixed(1)}
        <span className="text-lg">℃</span>
      </div>
      </div>
      </CareVial>
      <div className="flex justify-between px-2 text-xs text-muted">
        <span>ひんやり</span>
        <span className="font-bold text-leaf">ぴったり 25℃</span>
        <span>ぽかぽか</span>
      </div>
      {timer.running ? (
        <Button block size="lg" onClick={stop}>
          ここでストップ！
        </Button>
      ) : (
        <Button
          block
          size="lg"
          tone="banana"
          onClick={() => {
            Sound.init();
            finished.current = false;
            timer.start();
          }}
        >
          スタート
        </Button>
      )}
      <p className="text-xs text-muted">本物のショウジョウバエも、温度で育つ速さが変わります。</p>
      {timer.expired && (
        <p role="status" className="text-sm text-muted">
          時間が経ちました。ホームから問題を開き直してください。
        </p>
      )}
    </Card>
  );
}
