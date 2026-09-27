"use client";

import { FlyArt } from "@/components/art/FlyArt";
import { Card, SectionTitle } from "@/components/ui/primitives";
import { dailyTime } from "@/game/daily-circuit";
import type { DailyRanking } from "@/lib/api/hooks-daily";

export function DailyRankingList({ ranking }: { ranking: DailyRanking }) {
  return <section aria-label="今日のフレンドランキング">
    <SectionTitle>フレンドのタイム</SectionTitle>
    <Card className="overflow-hidden">
      {ranking.entries.length === 0 ? <p className="p-5 text-sm text-muted">今日の記録はまだありません。最初の回路をつなごう！</p> :
        <ol className="divide-y divide-line-soft">{ranking.entries.map(entry => <li key={entry.user_id} className={`flex items-center gap-2 px-3 py-2 ${entry.is_me ? "bg-tint-ai" : ""}`}>
          <span className="w-7 shrink-0 text-center font-mono font-bold text-ai">{entry.rank}<span className="sr-only">位</span></span>
          <FlyArt stage="adult" strain={entry.avatar.strain} sex={entry.avatar.sex} animated={false} className="h-12 w-14 shrink-0" />
          <span className="min-w-0 flex-1 truncate text-sm font-bold">{entry.display_name}{entry.is_me && <span className="ml-1 text-xs text-ai">（あなた）</span>}</span>
          <span className="shrink-0 font-mono text-sm tabular">{dailyTime(entry.elapsed_ms)}</span>
        </li>)}</ol>}
    </Card>
    <p className="mt-2 px-1 text-xs text-muted">本番の記録だけを表示。同タイムは先に提出した人が上位です。</p>
  </section>;
}
