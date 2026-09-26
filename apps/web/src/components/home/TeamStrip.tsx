import Link from "next/link";
import type { HomeData } from "@/lib/types";
import { Tsuyu } from "../art/Tsuyu";
import { ChevronRight } from "../ui/icons";
import { Card } from "../ui/primitives";

/** Research team at a glance: who is gathering and how full the bags are. */
export function TeamStrip({ team }: { team: HomeData["team"] }) {
  if (team.members.length === 0) {
    return (
      <Card className="flex items-center justify-between px-4 py-3 text-sm">
        <span className="text-muted">羽化した子をチームに入れると、材料を集めてくれます。</span>
      </Card>
    );
  }
  return (
    <Link href="/team" className="block">
      <Card className="flex items-center gap-3 px-4 py-3">
        <div className="flex -space-x-3">
          {team.members.slice(0, 5).map((m) => (
            <div key={m.id} className="size-11 rounded-full border-2 border-surface-2 bg-stage">
              <Tsuyu strain={m.strain} sex={m.sex} className="size-full" label={m.name} />
            </div>
          ))}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold">研究チーム</div>
          <div className="text-xs text-muted">
            {team.collectable ? (
              <span className="font-bold text-eye">袋に {team.bag_total} 個たまっています</span>
            ) : (
              "採集中…"
            )}
          </div>
        </div>
        <ChevronRight className="text-muted" />
      </Card>
    </Link>
  );
}
