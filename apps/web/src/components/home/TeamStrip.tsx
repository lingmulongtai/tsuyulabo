import Link from "next/link";
import type { HomeData } from "@/lib/types";
import { ChevronRight, TeamTabIcon } from "../ui/icons";
import { Card } from "../ui/primitives";

/** Research team at a glance: who is gathering and how full the bags are. */
export function TeamStrip({ team }: { team: HomeData["team"] }) {
  if (team.members.length === 0) {
    return (
      <Card className="flex items-center justify-between px-4 py-3 text-sm">
        <span className="text-muted">羽化した子をコロニーに入れると、材料を集めてくれます。</span>
      </Card>
    );
  }
  return (
    <Link href="/team" className="block">
      <Card className="flex items-center gap-3 px-4 py-3">
        <TeamTabIcon size={28} className="shrink-0 text-muted" />
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold">コロニー</div>
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
