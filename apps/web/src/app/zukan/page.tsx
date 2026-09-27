"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { Tsuyu } from "@/components/art/Tsuyu";
import { Card, Meter, SectionTitle } from "@/components/ui/primitives";
import { QueryState } from "@/components/ui/QueryState";
import { useZukan } from "@/lib/api/hooks";
import { BEHAVIOR_LABELS } from "@/lib/display";

export default function ZukanPage() {
  const zukan = useZukan();
  return <AppShell><CareFrame title="ツユの図鑑" subtitle="出会いと発見を、少しずつ集めよう">
    <QueryState query={zukan}>{data => <>
      <Card className="space-y-4 p-5"><Meter label="行動の発見" value={data.completion.behaviors * 100} color="var(--leaf)" /><Meter label="系統との出会い" value={data.completion.strains * 100} color="var(--banana)" /></Card>
      <SectionTitle>行動の記録</SectionTitle>
      <div className="grid grid-cols-3 gap-3">{data.behaviors.map(item => <Card key={item.id} className="p-3 text-center"><div className={`relative ${item.observed ? "" : "opacity-35"}`}>
        <Tsuyu className={`h-24 w-full ${item.observed ? "" : "brightness-0"}`} animated={false} />{!item.observed && <span className="absolute inset-0 grid place-items-center text-3xl text-white">？</span>}
      </div><p className="text-xs font-bold">{item.observed ? BEHAVIOR_LABELS[item.id] ?? "新しい行動" : "未発見"}</p></Card>)}</div>
      <SectionTitle>系統の記録</SectionTitle>
      <div className="grid grid-cols-2 gap-3">{data.strains.map(item => <Card key={item.id} className="p-3 text-center"><div className="relative">
        <Tsuyu strain={item.id} className={`h-36 w-full ${item.observed ? "" : "brightness-0 opacity-25"}`} animated={false} />{!item.observed && <span className="absolute inset-0 grid place-items-center text-4xl text-muted">？</span>}
      </div><p className="text-sm font-bold">{item.observed ? item.name : "まだ出会っていない系統"}</p></Card>)}</div>
    </>}</QueryState>
  </CareFrame></AppShell>;
}
