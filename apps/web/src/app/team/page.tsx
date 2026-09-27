"use client";
import { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame, ResultSheet } from "@/components/games/CareFrame";
import { AdultCard } from "@/components/collection/AdultCard";
import { Button, Card, Meter, SectionTitle } from "@/components/ui/primitives";
import { ErrorCard, QueryState } from "@/components/ui/QueryState";
import { useAdults, useCollect, useInventory, useLevelUp, useSetTeam, useTeam } from "@/lib/api/hooks";
import type { components } from "@/lib/api/schema";
import { bagCapacity, MATERIAL_LABELS } from "@/lib/display";
import * as Sound from "@/game/audio/sound";

type Schemas = components["schemas"];
export default function TeamPage() {
  const team = useTeam();
  const adults = useAdults();
  const inventory = useInventory();
  const collect = useCollect();
  const level = useLevelUp();
  const [reward, setReward] = useState<Schemas["Collection"] | null>(null);
  return <AppShell><CareFrame title="研究チーム" subtitle="５匹までの仲間と、材料あつめ">
    <QueryState query={team}>{data => <>
      <div className="grid grid-cols-5 gap-2" aria-label="チームの枠">{Array.from({ length: 5 }, (_, i) => <div key={i} className={`grid h-14 place-items-center rounded-2xl border-2 ${data.members[i] ? "border-leaf bg-tint-leaf" : "border-dashed border-line bg-surface"}`}><span className="text-sm font-bold">{data.members[i] ? `${i + 1} ✓` : "＋"}</span></div>)}</div>
      {data.members.length === 0 && <Card className="p-5 text-sm text-muted">羽化した子を下の飼育室から選んで、チームに入れよう。</Card>}
      {data.members.map(member => <AdultCard key={member.id} adult={member}>
        <Meter label="げんき" value={member.energy} color="var(--leaf)" />
        <div className="mt-2 rounded-2xl bg-bg p-3 text-sm"><p className="font-bold">材料袋 {Object.values(member.bag).reduce((sum, n) => sum + n, 0)} / {bagCapacity(member.subskills)}</p>
          <p className="text-muted">{Object.entries(member.bag).map(([id, n]) => `${MATERIAL_LABELS[id] ?? "材料"} ${n}`).join(" ・ ") || "材料を探しています…"}</p><p>しずく {member.shizuku} ・ 経験値 {member.pending_exp}</p></div>
      </AdultCard>)}
      <Button block size="lg" tone="banana" disabled={!data.collectable || collect.isPending} onClick={() => { Sound.init(); collect.mutate(undefined, { onSuccess: setReward }); }}>{collect.isPending ? "受け取り中…" : `袋をあける（${data.bag_total}個）`}</Button>
      {collect.error && <ErrorCard error={collect.error} retry={() => collect.mutate(undefined, { onSuccess: setReward })} />}
      <SectionTitle>飼育室</SectionTitle>
      <QueryState query={adults}>{flies => <TeamPicker key={data.members.map(m => m.id).join(",")} adults={flies} initial={data.members.map(m => m.id)}
        levelUp={id => level.mutate(id)} leveling={level.isPending} />}</QueryState>
      {level.error && <ErrorCard error={level.error} retry={() => level.variables && level.mutate(level.variables)} />}
      {level.data && <p role="status" className="text-center font-bold text-leaf">{level.data.name}が Lv.{level.data.level} になりました！</p>}
    </>}</QueryState>
    <SectionTitle>持っている材料</SectionTitle>
    <QueryState query={inventory}>{items => <Card className="grid grid-cols-2 gap-2 p-4">{Object.entries(items).map(([id, n]) => <p key={id} className="text-sm">{MATERIAL_LABELS[id] ?? "材料"} <b className="font-mono">{n}</b></p>)}{Object.keys(items).length === 0 && <p className="text-sm text-muted">まだ材料がありません。</p>}</Card>}</QueryState>
    {reward && <ResultSheet heading="採集おつかれさま！" great greatLabel="あつまった！" lines={[
      ...Object.entries(reward.materials).map(([id, n]) => ({ label: MATERIAL_LABELS[id] ?? "材料", value: `+${n}` })),
      { label: "しずく", value: `+${reward.shizuku}`, tone: "banana" },
      { label: "経験値", value: `+${Object.values(reward.exp).reduce((sum, n) => sum + n, 0)}`, tone: "leaf" },
    ]} primary={{ label: "しまっておく", onClick: () => setReward(null) }} />}
  </CareFrame></AppShell>;
}

function TeamPicker({ adults, initial, levelUp, leveling }: { adults: Schemas["Adult"][]; initial: string[]; levelUp: (id: string) => void; leveling: boolean }) {
  const [selected, setSelected] = useState(initial);
  const save = useSetTeam();
  return <div className="space-y-3">
    {adults.length === 0 && <Card className="p-5 text-sm text-muted">最初の羽化を楽しみに待とう。育てた子がここに集まります。</Card>}
    {adults.map(adult => <AdultCard adult={adult} key={adult.id}><div className="flex flex-wrap gap-2">
      <Button size="sm" tone={selected.includes(adult.id) ? "leaf" : "plain"} aria-pressed={selected.includes(adult.id)} disabled={save.isPending || (!selected.includes(adult.id) && selected.length >= 5)} onClick={() => setSelected(ids => ids.includes(adult.id) ? ids.filter(id => id !== adult.id) : [...ids, adult.id])}>{selected.includes(adult.id) ? "選択中 ✓" : "チームに選ぶ"}</Button>
      <Button size="sm" tone="banana" disabled={leveling || adult.level >= adult.level_cap} onClick={() => levelUp(adult.id)}>{adult.level >= adult.level_cap ? "レベル上限" : `Lv.UP ・ ${20 * adult.level}しずく`}</Button>
    </div></AdultCard>)}
    {adults.length > 0 && <Button block tone="leaf" disabled={save.isPending || selected.join() === initial.join()} onClick={() => save.mutate(selected)}>このチームにする（{selected.length}/5）</Button>}
    {save.error && <ErrorCard error={save.error} retry={() => save.mutate(selected)} />}
  </div>;
}
