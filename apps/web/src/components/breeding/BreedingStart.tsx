"use client";

import { useState } from "react";
import { useAdults, useStartWeek } from "@/lib/api/hooks";
import type { components } from "@/lib/api/schema";
import { OffspringPrediction } from "./OffspringPrediction";
import { PendingEggChoices } from "./PendingEggChoices";
import { FlyArt } from "../art/FlyArt";
import { STRAIN_LABELS } from "../art/palette";
import { Button, Card } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";

type Adult = components["schemas"]["Adult"];

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
    {!picking && <PendingEggChoices pending={start.isPending} onStart={pending_egg_id => start.mutate({ pending_egg_id })} />}
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
