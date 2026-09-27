"use client";

import { useState } from "react";
import { useAdults, useStartWeek } from "@/lib/api/hooks";
import type { components } from "@/lib/api/schema";
import { LOCI, predictOffspring, punnettSquare, type Genotype, type Locus } from "@/game/genetics";
import { FlyArt } from "../art/FlyArt";
import { STRAIN_LABELS } from "../art/palette";
import { Button, Card, TruthBadge } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";

type Adult = components["schemas"]["Adult"];
const percent = (value: number) => `${(value * 100).toLocaleString("ja-JP", { maximumFractionDigits: 2 })}%`;

export function BreedingStart() {
  const [picking, setPicking] = useState(false);
  const start = useStartWeek();
  return <Card className="space-y-4 p-5 text-center">
    <FlyArt stage="egg" className="mx-auto h-32 w-32" />
    <h2 className="font-kiwi text-xl">新しい一週間をはじめよう</h2>
    <p className="text-sm text-muted">小さな卵から、どんなツユに育つかな。</p>
    {!picking ? <>
      <Button block size="lg" disabled={start.isPending} onClick={() => start.mutate()}>{start.isPending ? "卵を受け取り中…" : "卵を受け取る"}</Button>
      <Button block tone="leaf" disabled={start.isPending} onClick={() => { start.reset(); setPicking(true); }}>交配する</Button>
    </> : <ParentPicker pending={start.isPending} onStart={parents => start.mutate({ parents })} />}
    {start.error && <ErrorCard error={start.error} />}
    {picking && <Button tone="plain" block disabled={start.isPending} onClick={() => { start.reset(); setPicking(false); }}>戻る</Button>}
  </Card>;
}

function ParentPicker({ pending, onStart }: { pending: boolean; onStart: (parents: [string, string]) => void }) {
  const adults = useAdults();
  const [motherId, setMotherId] = useState("");
  const [fatherId, setFatherId] = useState("");
  return <QueryState query={adults}>{data => {
    const mother = data.find(adult => adult.id === motherId && adult.sex === "f");
    const father = data.find(adult => adult.id === fatherId && adult.sex === "m");
    return <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2">
        <ParentCard label="母親 ♀" candidates={data.filter(adult => adult.sex === "f")} selected={mother} disabled={pending} onSelect={setMotherId} />
        <ParentCard label="父親 ♂" candidates={data.filter(adult => adult.sex === "m")} selected={father} disabled={pending} onSelect={setFatherId} />
      </div>
      <p className="text-xs text-muted">親になれるのは、それぞれ週に1回。月曜の朝4時に切り替わります。</p>
      {mother && father && <OffspringPrediction mother={mother.genotype} father={father.genotype} />}
      <Button block tone="leaf" disabled={pending || !mother || !father} onClick={() => { if (mother && father) onStart([mother.id, father.id]); }}>{pending ? "交配中…" : "このふたりの卵を受け取る"}</Button>
    </div>;
  }}</QueryState>;
}

function ParentCard({ label, candidates, selected, disabled, onSelect }: { label: string; candidates: Adult[]; selected?: Adult; disabled: boolean; onSelect: (id: string) => void }) {
  return <Card className="min-w-0 space-y-2 p-3">
    <label className="block text-sm font-bold">{label}
      <select aria-label={label} className="mt-2 w-full rounded-xl border border-line bg-bg p-2 text-sm focus:outline-leaf" value={selected?.id ?? ""} disabled={disabled || !candidates.length} onChange={event => onSelect(event.target.value)}>
        <option value="">選んでね</option>
        {candidates.map(adult => <option key={adult.id} value={adult.id}>{adult.name}（{adult.phenotypes.map(p => STRAIN_LABELS[p].name).join("・")}）</option>)}
      </select>
    </label>
    {selected ? <>
      <FlyArt stage="adult" sex={selected.sex} strain={selected.strain} className="mx-auto h-24 w-full" />
      <p className="text-xs text-muted">{selected.phenotypes.map(p => STRAIN_LABELS[p].name).join("・")}</p>
    </> : <p className="py-6 text-xs text-muted">{candidates.length ? "どの子にする？" : "成虫がまだいません"}</p>}
  </Card>;
}

function OffspringPrediction({ mother, father }: { mother: Genotype; father: Genotype }) {
  const [locus, setLocus] = useState<Locus>("w");
  const prediction = predictOffspring(mother, father);
  const square = punnettSquare(mother, father, locus);
  return <section className="space-y-3 rounded-2xl bg-bg p-3 text-left" aria-label="子どもの予測">
    <h3 className="font-kiwi">子どもの予測 <TruthBadge kind="model" /></h3>
    <p className="text-xs text-muted">羽化する子の確率です。遺伝子の連鎖と羽化時の新しい突然変異は含みません。</p>
    <table className="w-full text-sm">
      <caption className="sr-only">性別と見た目の確率</caption>
      <thead><tr className="border-b border-line"><th scope="col">性別</th><th scope="col" className="text-left">見た目</th><th scope="col" className="text-right">確率</th></tr></thead>
      <tbody>{prediction.outcomes.map(outcome => <tr key={`${outcome.sex}:${outcome.phenotypes.join()}`}>
        <td className="py-1 text-center">{outcome.sex === "f" ? "♀" : "♂"}</td>
        <td className="px-2">{outcome.phenotypes.map(p => STRAIN_LABELS[p].name).join("・")}</td>
        <td className="text-right font-mono">{percent(outcome.probability)}</td>
      </tr>)}</tbody>
    </table>
    {prediction.lethalProbability > 0 && <p className="rounded-xl bg-tint-banana p-2 text-xs">Cy/Cy になる卵は {percent(prediction.lethalProbability)}。育たないため、育つ卵を受け取ります。上の確率は育つ子だけで計算しています。</p>}
    <details className="text-sm">
      <summary className="cursor-pointer font-bold text-leaf">遺伝子の組み合わせを見る</summary>
      <label className="my-2 block">遺伝子 <select className="rounded-lg border border-line bg-surface-2 p-1" value={locus} onChange={event => setLocus(event.target.value as Locus)}>{LOCI.map(value => <option key={value}>{value}</option>)}</select></label>
      <table className="w-full border-collapse text-center font-mono">
        <caption className="mb-1 font-sans text-xs text-muted">母親のコピー × 父親のコピー（各マスは同じ確率）</caption>
        <thead><tr><th scope="col">♀ × ♂</th>{square.paternal.map((allele, index) => <th scope="col" key={index} className="border border-line p-2">{allele}</th>)}</tr></thead>
        <tbody>{square.maternal.map((allele, row) => <tr key={row}><th scope="row" className="border border-line p-2">{allele}</th>{square.paternal.map((other, column) => <td key={column} className="border border-line p-2">{allele}/{other}{allele === "Cy" && other === "Cy" && <span className="block font-sans text-xs text-muted">育たない</span>}</td>)}</tr>)}</tbody>
      </table>
      <p className="mt-2 text-xs text-muted">＋ は野生型。劣性の変異は ＋ と組になると見た目に現れず、次の世代へ受け継がれます。</p>
    </details>
  </section>;
}
