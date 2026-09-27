import Link from "next/link";
import { Tsuyu } from "@/components/art/Tsuyu";
import { Card, TruthBadge } from "@/components/ui/primitives";

export function RaceCard() {
  return <Link href="/race" className="block"><Card className="flex items-center gap-3 p-4">
    <Tsuyu className="h-16 w-16 shrink-0" />
    <div className="flex-1"><div className="flex items-center gap-2"><h2 className="font-kiwi text-lg">今週の迷路レース</h2><TruthBadge kind="model" /></div><p className="mt-1 text-xs text-muted">好きな匂いを道しるべに。フレンドと走りを比べよう。</p></div><span className="font-bold text-ai" aria-hidden>→</span>
  </Card></Link>;
}
