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
import { ActionGrid, ACTION_META } from "./ActionGrid";
import { TodoList } from "./TodoList";
import { CareSheet } from "./CareSheet";
import { stageFraming } from "../vivarium/framing";
import glass from "../ui/material.module.css";
import motion from "../ui/motion.module.css";
import { QuietHint } from "../shiori/QuietHint";
import { BehaviourWhy } from "../shiori/BehaviourWhy";

export function ColonyVivarium({ data, children }: { data: HomeData; children?: React.ReactNode }) {
  const adults = useAdults();
  const [selected, setSelected] = useState<string | null>(null);
  const all = adults.data ?? data.team.members;
  const adult = all.find(fly => fly.id === selected);
  const id = adult?.id ?? data.week?.id ?? all[0]?.id ?? "";
  const shownAdult = adult ?? (!data.week ? all[0] : undefined);
  const visible = usePageVisible();
  const [paused, setPaused] = useState(false);
  const [odourAction, setOdourAction] = useState<Behaviour>();
  const [whyFor, setWhyFor] = useState<string>();
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
  const upcoming = data.todo.filter(item => item.status === "available").filter((item, i, items) => items.findIndex(other => other.action === item.action) === i).slice(0, 2);
  const stage = shownAdult ? "adult" : data.fly?.stage ?? "egg";
  const needs = !shownAdult && saved ? `${saved.food.moisture < 0.3 ? "餌が乾いてきました。" : "餌はしっとりしています。"} ${saved.mould > 0.2 ? "カビが見えます。ガラスを拭きましょう。" : saved.grime > 0.5 ? "ガラスが曇ってきました。" : ""}` : "";
  const eclosion = !shownAdult && data.week?.ready_to_eclose ? <Link href="/presentation" className="block min-h-11 rounded-xl border border-banana/40 px-3 py-2 text-sm text-banana">羽化の日へ →</Link> : null;
  return <section aria-label="コロニーの飼育びん" className="absolute inset-0" data-home-vial>
    <Vivarium key={id} seed={id || "empty"} stage={stage} framing={stageFraming(stage)} sex={shownAdult?.sex} traits={shownAdult?.phenotypes}
      environment={habitat(saved)} pupationPosition={sitePosition(saved?.pupation_position)} behaviour={odourAction ?? decodedBehaviour(brain.data)} paused={paused}
      pointOfInterest={odourAction ? [0.48, -1.08, -0.2] : undefined} onSubjectPick={() => setWhyFor(id)} />
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,.38),transparent_25%,transparent_55%,rgba(0,0,0,.6))]" />
    <div className={`${motion.enter} absolute inset-x-4 top-[calc(120px+env(safe-area-inset-top))] flex items-start justify-between gap-2 text-xs`}>
      <button type="button" className={`${glass.glass} min-h-11 rounded-xl px-3 py-2 text-left`} aria-expanded={whyFor === id} onClick={() => setWhyFor(whyFor === id ? undefined : id)}>
        <span className="block">{shownAdult?.name ?? "この子の一週間"}</span><span className="text-[10px] text-[#d5cab4]">{shownAdult ? "成虫" : data.fly?.mood_label} ・ この子を選ぶ</span>
      </button>
      <button className={`${glass.glass} grid size-11 place-items-center rounded-full`} aria-label={paused ? "動きを再開" : "動きを一時停止"} aria-pressed={paused} onClick={() => setPaused(value => !value)}>{paused ? "▷" : "Ⅱ"}</button>
    </div>
    {whyFor === id && <div className="absolute inset-x-4 top-[calc(180px+env(safe-area-inset-top))] z-20"><BehaviourWhy key={`${id}:${odourAction ?? decodedBehaviour(brain.data)}`} flyId={id} behaviour={odourAction ?? decodedBehaviour(brain.data)} source={odourAction ? "copy_odor_choice" : "brain_decoder"} onClose={() => setWhyFor(undefined)} /></div>}
    {ids.length > 1 && <div className={`${glass.glass} absolute left-1/2 bottom-[calc(clamp(172px,24dvh,220px)+76px+env(safe-area-inset-bottom))] flex -translate-x-1/2 items-center rounded-full px-1 text-xs`} style={{ touchAction: "pan-y" }}
      onPointerDown={e => { if ((e.target as Element).closest("button")) return; start.current = e.clientX; e.currentTarget.setPointerCapture(e.pointerId); }}
      onPointerUp={e => { if (start.current !== null && Math.abs(e.clientX - start.current) > 40) move(e.clientX < start.current ? 1 : -1); start.current = null; }} onPointerCancel={() => { start.current = null; }}>
      <button className="size-11" aria-label="前のびん" onClick={() => move(-1)}>←</button><span className="whitespace-nowrap">{ids.indexOf(id) + 1} / {ids.length}</span><button className="size-11" aria-label="次のびん" onClick={() => move(1)}>→</button>
    </div>}
    <CareSheet preview={<div className="space-y-2">
      {eclosion ?? (shownAdult ? <Link href={`/adults/${shownAdult.id}`} className="block min-h-11 py-2 text-sm">この子の育ちを見る →</Link> : <div className="grid grid-cols-2 gap-2">{upcoming.map(item => <Link key={item.action} href={ACTION_META[item.action].href} className="flex min-h-11 items-center justify-between rounded-xl border border-white/20 px-3 text-sm"><span>{ACTION_META[item.action].label}</span><span className="text-banana">→</span></Link>)}</div>)}
      {!eclosion && !shownAdult && upcoming.length === 0 && <p className="text-sm">今はそっと見守りましょう。</p>}
      {needs && <p className="text-[11px] text-[#d5cab4]" data-vial-needs>{needs}</p>}
      <p className="text-[10px] text-[#d5cab4]">上へ引いて、すべてのお世話と観察を見る</p>
    </div>}>
      <div className="space-y-3">
        {eclosion}
        {!shownAdult && <><ActionGrid compact todo={data.todo} /><TodoList todo={data.todo} /></>}
        {id && <><QuietHint key={`hint-${id}`} flyId={id} /><OdourMoment key={id} flyId={id} cue={cue} onBehaviour={setOdourAction} disabled={saved?.learning_pending} paused={paused} /></>}
        {needs && <p className="text-xs text-muted">{needs}</p>}
        {shownAdult && <Link href={`/adults/${shownAdult.id}`} className="block min-h-11 py-2 text-sm">この子の育ちを見る →</Link>}
        {children}
      </div>
    </CareSheet>
  </section>;
}
