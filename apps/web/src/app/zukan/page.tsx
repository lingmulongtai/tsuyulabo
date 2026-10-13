"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { AdultCard } from "@/components/collection/AdultCard";
import { Portrait } from "@/components/vivarium/Portrait";
import { Card, SectionTitle } from "@/components/ui/primitives";
import { QueryState } from "@/components/ui/QueryState";
import { useAdults, useZukan } from "@/lib/api/hooks";
import { BEHAVIOR_LABELS } from "@/lib/display";

export default function ZukanPage() {
  const zukan = useZukan(), adults = useAdults();
  return <AppShell><CareFrame title="ツユの図鑑" subtitle="育てた系統と、それぞれの動きを残す">
    <SectionTitle>育てた子たち</SectionTitle>
    <QueryState query={adults}>{flies => flies.length ? <div className="grid gap-3">{flies.map(adult => <AdultCard key={adult.id} adult={adult} />)}</div> : <p className="text-sm text-muted">最初の羽化を待っています。出会った姿をここに残しましょう。</p>}</QueryState>
    <QueryState query={zukan}>{data => <>
      <details className="text-xs text-muted"><summary>これまでの出会い</summary><p>見つけた動き {data.behaviors.filter(item => item.observed).length} ・ 出会った系統 {data.strains.filter(item => item.observed).length}</p></details>
      <SectionTitle>行動の記録</SectionTitle>
      <p className="text-[11px] text-muted">動きの名前を残した記録。姿は系統の代表です。</p>
      <div className="grid grid-cols-3 gap-2">{data.behaviors.map(item => <Card key={item.id} className="space-y-2 p-2 text-center">
        <Portrait seed="behavior-reference" stage="adult" label="行動図鑑の代表個体" known={item.observed} />
        <p className="text-[11px]">{item.observed ? BEHAVIOR_LABELS[item.id] ?? "新しい行動" : "未発見"}</p>
      </Card>)}</div>
      <SectionTitle>系統の記録</SectionTitle>
      <div className="grid grid-cols-2 gap-3">{data.strains.map(item => <Card key={item.id} className="space-y-2 p-2 text-center">
        <Portrait seed={`strain-${item.id}`} stage="adult" traits={[item.id]} label={`${item.name}の代表個体`} known={item.observed} />
        <p className="text-xs">{item.observed ? item.name : "まだ出会っていない系統"}</p>
      </Card>)}</div>
    </>}</QueryState>
  </CareFrame></AppShell>;
}
