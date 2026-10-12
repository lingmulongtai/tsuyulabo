"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { Tsuyu } from "@/components/art/Tsuyu";
import { Card, SectionTitle } from "@/components/ui/primitives";
import { QueryState } from "@/components/ui/QueryState";
import { useZukan } from "@/lib/api/hooks";
import { BEHAVIOR_LABELS } from "@/lib/display";

export default function ZukanPage() {
  const zukan = useZukan();
  return <AppShell><CareFrame title="ツユの図鑑" subtitle="育てた系統と、それぞれの動きを残す">
    <QueryState query={zukan}>{data => <>
      <Card className="space-y-3 p-5 text-sm"><p>育てた子が見せた動きと、受け継いだ系統の図鑑です。毎日の世話で、その子だけの個性が見えてきます。</p><details className="text-xs text-muted"><summary>これまでの出会い</summary><p>見つけた動き {data.behaviors.filter(item => item.observed).length} ・ 出会った系統 {data.strains.filter(item => item.observed).length}</p></details></Card>
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
