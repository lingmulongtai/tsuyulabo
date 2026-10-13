"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAdults, useBehavior, useHome } from "@/lib/api/hooks";
import { decodedBehaviour, habitat, sitePosition } from "@/game/vial";
import type { HomeData } from "@/lib/types";
import { Vivarium, type Behaviour } from "../vivarium/Vivarium";
import { OdourMoment } from "../vivarium/OdourMoment";
import { usePageVisible } from "../vivarium/lifecycle";
import type { Cue } from "@/game/puzzles/types";
import { CUE_INFO } from "@/game/labels";
import { ActionGrid } from "./ActionGrid";

export function ColonyVivarium({ data }: { data: HomeData }) {
  const adults = useAdults();
  const [selected, setSelected] = useState<string | null>(null);
  const all = adults.data ?? data.team.members;
  const adult = all.find(fly => fly.id === selected);
  const id = adult?.id ?? data.week?.id ?? all[0]?.id ?? "";
  const shownAdult = adult ?? (!data.week ? all[0] : undefined);
  const visible = usePageVisible();
  const [paused, setPaused] = useState(false);
  const [odourAction, setOdourAction] = useState<Behaviour>();
  const brain = useBehavior(id);
  const refresh = brain.refetch;
  useEffect(() => {
    if (!id || !visible || paused) return;
    const timer = setInterval(() => void refresh(), 30_000);
    return () => clearInterval(timer);
  }, [id, visible, paused, refresh]);
  const start = useRef<number | null>(null);
  const ids = [...(data.week ? [data.week.id] : []), ...all.map(fly => fly.id)];
  const move = (direction: number) => {
    if (ids.length < 2) return;
    const next = ids[(Math.max(0, ids.indexOf(id)) + direction + ids.length) % ids.length];
    setSelected(next === data.week?.id ? null : next); setOdourAction(undefined);
  };
  const saved = shownAdult?.vial ?? data.vial;
  const home = useHome();
  const refreshHome = home.refetch, refreshAdults = adults.refetch;
  useEffect(() => {
    if (!saved?.learning_pending || !visible) return;
    const timer = setInterval(() => { void refreshHome(); void refreshAdults(); }, 1500);
    return () => clearInterval(timer);
  }, [saved?.learning_pending, visible, refreshHome, refreshAdults]);
  const cue = saved?.cue && Object.hasOwn(CUE_INFO, saved.cue) ? saved.cue as Cue : "banana";
  const next = data.todo.find(item => item.status === "available");
  return <section aria-label="コロニーの飼育びん" className="relative overflow-hidden rounded-xl" style={{ height: "max(650px, calc(100svh - 140px))" }} data-home-vial>
    <div className="absolute inset-x-0 top-0 bottom-[240px]"><Vivarium key={id} seed={id || "empty"} stage={shownAdult ? "adult" : data.fly?.stage ?? "egg"} sex={shownAdult?.sex} traits={shownAdult?.phenotypes}
      environment={habitat(saved)} pupationPosition={sitePosition(saved?.pupation_position)} behaviour={odourAction ?? decodedBehaviour(brain.data)} paused={paused}
      pointOfInterest={odourAction ? [0.48, -1.08, -0.2] : undefined} /></div>
    <div className="absolute inset-x-3 top-3 flex justify-between gap-2 text-sm">
      <div className="glass-panel rounded-lg p-3"><p>{shownAdult?.name ?? (data.fly ? "この子の一週間" : "卵を迎える準備")}</p><p className="text-xs text-muted">{data.clock.slot === "night" ? "夜" : data.clock.slot === "morning" ? "朝" : "昼"} ・ {shownAdult ? "成虫" : data.fly?.mood_label}</p></div>
      <button className="glass-panel h-11 rounded-lg px-3 text-xs" aria-pressed={paused} onClick={() => setPaused(value => !value)}>{paused ? "動きを再開" : "動きを一時停止"}</button>
    </div>
    <div className="absolute inset-x-3 bottom-3 space-y-2">
      {ids.length > 1 && <div className="glass-panel flex min-h-11 items-center justify-between rounded-lg px-2" style={{ touchAction: "pan-y" }} onPointerDown={e => { if ((e.target as Element).closest("button")) return; start.current = e.clientX; e.currentTarget.setPointerCapture(e.pointerId); }} onPointerUp={e => { if (start.current !== null && Math.abs(e.clientX - start.current) > 40) move(e.clientX < start.current ? 1 : -1); start.current = null; }} onPointerCancel={() => { start.current = null; }}>
        <button className="min-h-11 px-3" aria-label="前のびん" onClick={() => move(-1)}>←</button><span className="text-xs">{ids.indexOf(id) + 1} / {ids.length} ・ 左右にスワイプ</span><button className="min-h-11 px-3" aria-label="次のびん" onClick={() => move(1)}>→</button>
      </div>}
      {id && <div className="glass-panel rounded-lg p-3"><OdourMoment key={id} flyId={id} cue={cue} onBehaviour={setOdourAction} disabled={saved?.learning_pending} paused={paused} /></div>}
      {!shownAdult && data.week && <details className="glass-panel rounded-lg p-3" open><summary className="text-sm">今日のお世話{next ? " ・ 次にできること" : " ・ ひと休み"}</summary><div className="pt-2"><ActionGrid compact todo={data.todo} /></div></details>}
      {shownAdult && <Link href={`/adults/${shownAdult.id}`} className="glass-panel block min-h-11 rounded-lg p-3 text-center text-sm">この子の育ちを見る</Link>}
      {!shownAdult && saved && <p className="glass-panel rounded-lg px-3 py-2 text-xs" data-vial-needs>{saved.food.moisture < 0.3 ? "餌が乾いてきました。" : "餌はしっとりしています。"} {saved.mould > 0.2 ? "カビが見えます。ガラスを拭きましょう。" : saved.grime > 0.5 ? "ガラスが曇ってきました。" : ""}</p>}
    </div>
  </section>;
}
