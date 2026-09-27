import Link from "next/link";
import { Card, TruthBadge } from "@/components/ui/primitives";

export function SumoCard() {
  return <Link href="/sumo" className="block focus-visible:rounded-3xl focus-visible:outline-2 focus-visible:outline-ai"><Card className="flex items-center justify-between p-4">
    <div><div className="flex items-center gap-2"><b className="font-kiwi">なわばりずもう</b><TruthBadge kind="model" /></div><p className="mt-1 text-xs text-muted">オスどうしの押し合い。脳モデルで勝負！</p></div>
    <span className="text-xl text-ai" aria-hidden>→</span>
  </Card></Link>;
}
