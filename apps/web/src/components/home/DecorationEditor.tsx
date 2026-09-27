"use client";

import { useState } from "react";
import { ErrorCard, QueryState } from "../ui/QueryState";
import { Button, Card } from "../ui/primitives";
import { useDecorations, useEquipDecorations, type DecorationInventory, type Layout } from "@/lib/api/hooks-contest";
import type { Stage } from "../art/FlyArt";
import { Terrarium } from "./Terrarium";

const LABELS: Record<keyof Layout, string> = {
  background: "背景", vial: "ビン", left: "左の飾り", right: "右の飾り", accessory: "ツユの飾り",
};
const KIND: Record<keyof Layout, string> = {
  background: "background", vial: "vial", left: "ornament", right: "ornament", accessory: "accessory",
};

export function DecorationEditor({ stage, researchDay, moodLabel, night }: {
  stage: Stage; researchDay: number; moodLabel?: string; night: boolean;
}) {
  const inventory = useDecorations();
  return <QueryState query={inventory}>{data => <Editor key={JSON.stringify(data.layout)} data={data} stage={stage} researchDay={researchDay} moodLabel={moodLabel} night={night} />}</QueryState>;
}

function Editor({ data, stage, researchDay, moodLabel, night }: {
  data: DecorationInventory; stage: Stage; researchDay: number; moodLabel?: string; night: boolean;
}) {
  const [layout, setLayout] = useState<Layout>(data.layout);
  const [open, setOpen] = useState(false);
  const save = useEquipDecorations();
  const owned = new Set(data.owned.map(item => item.id));
  return <section className="space-y-3" aria-label="飼育室の飾りつけ">
    <Terrarium stage={stage} researchDay={researchDay} moodLabel={moodLabel} night={night} layout={layout} />
    <Button tone="plain" block onClick={() => setOpen(value => !value)} aria-expanded={open}>飼育室を飾る {open ? "−" : "＋"}</Button>
    {open && <Card className="space-y-4 p-4">
      <p className="text-sm text-muted">好きな装飾を選んで、飼育室を自分らしく。飾りは育成の結果に影響しません。</p>
      {(Object.keys(LABELS) as (keyof Layout)[]).map(slot => <label key={slot} className="block space-y-1 text-sm font-bold">
        <span>{LABELS[slot]}</span>
        <select className="w-full rounded-xl border border-line bg-surface-2 p-2" value={layout[slot] ?? ""}
          onChange={event => setLayout(value => ({ ...value, [slot]: event.target.value || null }))}>
          <option value="">なし</option>
          {data.catalog.filter(item => item.kind === KIND[slot] && owned.has(item.id)).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </label>)}
      <Button tone="leaf" block disabled={save.isPending} onClick={() => save.mutate(layout)}>この配置を保存</Button>
      {save.isSuccess && <p role="status" className="text-sm text-leaf">保存しました</p>}
      {save.error && <ErrorCard error={save.error} retry={() => save.mutate(layout)} />}
    </Card>}
  </section>;
}
