"use client";

import { useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Vivarium, type Behaviour, type Phenotype, type Quality, type Stage, type VivariumHandle } from "@/components/vivarium/Vivarium";
import styles from "./preview.module.css";

const stages: [Stage, string][] = [["egg", "卵"], ["larva", "幼虫"], ["pupa", "さなぎ"], ["adult", "成虫"]];
const actions: [Behaviour, string][] = [["rest", "休む"], ["walk", "歩く"], ["turn_left", "左を向く"], ["turn_right", "右を向く"], ["groom", "毛づくろい"], ["feed", "食べる"], ["escape", "逃げる"], ["approach", "匂いに近づく"], ["avoid", "匂いを避ける"], ["fly", "飛ぶ"], ["burrow", "潜る"]];
const mutations: [Phenotype, string][] = [["white", "白い目"], ["yellow", "黄色い体"], ["ebony", "黒い体"], ["curly", "巻いた翅"], ["vestigial", "小さな翅"]];
export function Preview() {
  const search = useSearchParams();
  const [stage, setStage] = useState<Stage>(() => stages.find(([s]) => s === search.get("stage"))?.[0] ?? "adult");
  const [behaviour, setBehaviour] = useState<Behaviour>(() => actions.find(([s]) => s === search.get("behaviour"))?.[0] ?? "rest");
  const [quality, setQuality] = useState<Quality | "auto">(() => (["high", "medium", "low"] as const).find(q => q === search.get("quality")) ?? "auto");
  const [resolved, setResolved] = useState<Quality>("medium");
  const [framing, setFraming] = useState<"wide" | "close">(search.get("framing") === "close" ? "close" : "wide");
  const [sex, setSex] = useState<"f" | "m">("f");
  const [traits, setTraits] = useState<Phenotype[]>([]);
  const [humidity, setHumidity] = useState(0.64), [moisture, setMoisture] = useState(0.68), [yeast, setYeast] = useState(0.5);
  const [color, setColor] = useState("#bda45c"), [mould, setMould] = useState(0), [grime, setGrime] = useState(0), [pupaAge, setPupaAge] = useState(0.4);
  const [paused, setPaused] = useState(search.get("paused") === "1");
  const [seed, setSeed] = useState("tsuyu-01");
  const vivarium = useRef<VivariumHandle>(null);
  const clean = search.get("clean") === "1";
  return <main className={styles.preview}>
    <div className={styles.scene}>
      <Vivarium ref={vivarium} stage={stage} behaviour={behaviour} sex={sex} traits={traits} seed={seed} framing={framing} quality={quality} onQualityChange={setResolved} paused={paused} environment={{ humidity, food: { color, moisture, yeast }, mould, grime, pupaAge }} />
    </div>
    {!clean && <>
      <header className={styles.heading}><span>TSUYU LABO / VIVARIUM</span><h1>小さな命を、間近に。</h1><p>回して、寄って、そっと見守る。</p></header>
      <div className={styles.toolbar}>
        <button onClick={() => setFraming(framing === "wide" ? "close" : "wide")}>{framing === "wide" ? "近くで見る" : "びん全体を見る"}</button>
        <button onClick={() => setPaused(!paused)} aria-pressed={paused}>{paused ? "動きを再開" : "一時停止"}</button>
      </div>
      <details className={styles.panel}>
        <summary>飼育びんの設定 <small>{resolved}</small></summary>
        <div className={styles.fields}>
          <label>成長段階<select aria-label="成長段階" value={stage} onChange={e => setStage(e.target.value as Stage)}>{stages.map(([s, label]) => <option key={s} value={s}>{label}</option>)}</select></label>
          <label>行動<select aria-label="行動" value={behaviour} onChange={e => setBehaviour(e.target.value as Behaviour)}>{actions.map(([s, label]) => <option key={s} value={s}>{label}</option>)}</select></label>
          <label>性別<select aria-label="性別" value={sex} onChange={e => setSex(e.target.value as "f" | "m")}><option value="f">メス</option><option value="m">オス</option></select></label>
          <label>画質<select aria-label="画質" value={quality} onChange={e => setQuality(e.target.value as Quality | "auto")}><option value="auto">自動</option><option value="high">高</option><option value="medium">標準</option><option value="low">軽量</option></select></label>
          <fieldset><legend>発現している形質</legend>{mutations.map(([trait, label]) => <label className={styles.check} key={trait}><input type="checkbox" checked={traits.includes(trait)} onChange={e => setTraits(e.target.checked ? [...traits, trait] : traits.filter(t => t !== trait))} />{label}</label>)}</fieldset>
          {[["湿度", humidity, setHumidity], ["餌の水分", moisture, setMoisture], ["イースト", yeast, setYeast], ["カビ", mould, setMould], ["ガラスの汚れ", grime, setGrime], ["さなぎの成熟", pupaAge, setPupaAge]].map(([label, value, setter]) => <label key={String(label)}>{String(label)}<output>{Math.round(Number(value) * 100)}%</output><input aria-label={String(label)} type="range" min="0" max="1" step="0.01" value={Number(value)} onChange={e => (setter as (v: number) => void)(Number(e.target.value))} /></label>)}
          <label>餌の色<input type="color" value={color} onChange={e => setColor(e.target.value)} /></label>
          <label>個体<input value={seed} onChange={e => setSeed(e.target.value)} maxLength={40} /></label>
          <button onClick={() => { vivarium.current?.pointOfInterest([0.65, -1.08, -0.2]); setBehaviour("approach"); vivarium.current?.setBehaviour("approach"); }}>奥に匂いを置く</button>
        </div>
      </details>
      <footer className={styles.caption}>DROSOPHILA MELANOGASTER <span>指で回転 · ピンチで拡大</span></footer>
    </>}
  </main>;
}
