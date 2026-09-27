"use client";

import { useEffect, useState } from "react";
import { Button, Card, TruthBadge } from "@/components/ui/primitives";
import { BrainDiagram } from "./BrainDiagram";
import { CIRCUITS, REAL_NAMES, type BrainActivity } from "./types";

export function BrainPlayback({ activity }: { activity: BrainActivity }) {
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selected, setSelected] = useState("MN9");
  const windows = activity.groups[0]?.rates.length ?? 0;
  const group = activity.groups.find((item) => item.name === selected) ?? activity.groups[0];
  useEffect(() => {
    if (!playing || windows < 2) return;
    const timer = window.setInterval(() => setFrame((value) => (value + 1) % windows), 250);
    return () => window.clearInterval(timer);
  }, [playing, windows]);
  if (!windows || !group) return <p role="status">表示できる神経活動がありません。</p>;
  const windowMs = activity.duration_ms / windows;
  return (
    <div className="space-y-3">
      <Card className="sticky top-0 z-10 space-y-2 p-3">
        <div className="flex items-center justify-between gap-2">
          <Button size="sm" onClick={() => setPlaying(!playing)} aria-pressed={playing}>{playing ? "一時停止" : "再生"}</Button>
          <output className="font-mono text-xs tabular" aria-live="off">{Math.round(frame * windowMs)}–{Math.round((frame + 1) * windowMs)} / {activity.duration_ms} ms</output>
        </div>
        <label className="block text-xs text-muted" htmlFor="brain-time">観察する時間（{frame + 1} / {windows}）</label>
        <input id="brain-time" type="range" min="0" max={windows - 1} value={frame}
          aria-valuetext={`${Math.round(frame * windowMs)}から${Math.round((frame + 1) * windowMs)}ミリ秒`}
          className="block w-full accent-leaf" onChange={(event) => { setPlaying(false); setFrame(Number(event.target.value)); }} />
        <p className="text-xs text-muted">ゆっくり再生して観察できます。数字は群内の平均発火率（Hz）。</p>
      </Card>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
        <span className="text-leaf">実線 → 興奮</span><span className="text-eye">破線 ⊣ 抑制</span>
        <span className="text-muted">太さ：重みの大きさ</span>
      </div>
      <p className="text-xs text-muted">図は左右にスクロールできます。細胞群を選ぶと詳しく見られます。</p>
      <BrainDiagram activity={activity} frame={frame} selected={group.name} onSelect={setSelected} />
      <Card className="space-y-2 p-4">
        <label htmlFor="brain-group" className="block text-xs text-muted">詳しく見る細胞群</label>
        <select id="brain-group" value={group.name} onChange={(event) => setSelected(event.target.value)} className="w-full rounded-xl border border-line bg-surface p-2 text-sm">
          {activity.groups.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
        </select>
        <div className="flex flex-wrap items-center gap-2"><strong className="font-mono">{group.name}</strong><TruthBadge kind={REAL_NAMES.has(group.name) ? "real" : "model"} /></div>
        <p className="text-sm">{CIRCUITS[group.circuit]} · <span className="font-mono tabular">{(group.rates[frame] ?? 0).toFixed(1)} Hz</span></p>
        <p className="text-xs text-muted">{REAL_NAMES.has(group.name) ? "実在の細胞群にちなんだ名前です。活動と配線の数値はモデルによるものです。" : "この模型でまとめて表現した細胞群です。"}</p>
      </Card>
      <Card className="space-y-2 p-4 text-xs text-muted">
        <TruthBadge kind="model" />
        <p>これは小さな合成配線 toy-v0 のシミュレーションです。本物の脳の測定データではありません。細胞数と重みを簡略化し、この子の個体差と学習済みの重みを使っています。</p>
        <p>光るほど発火率が高く、200 Hz 以上で最も明るくなります。線は学習済みの配線の重みを表し、個体ごとの増幅率は含みません。</p>
        <p>DAN はしつけのときに学習を調節します。この観察ではしつけをせず、育てた子の状態も変わりません。</p>
      </Card>
    </div>
  );
}
