"use client";

import { useState } from "react";
import { LOCI, predictOffspring, punnettSquare, type Genotype, type Locus } from "@/game/genetics";
import { STRAIN_LABELS } from "../art/palette";
import { TruthBadge } from "../ui/primitives";

const percent = (value: number) => `${(value * 100).toLocaleString("ja-JP", { maximumFractionDigits: 2 })}%`;

export function OffspringPrediction({ mother, father }: { mother: Genotype; father: Genotype }) {
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
