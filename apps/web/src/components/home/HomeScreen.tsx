"use client";
import Link from "next/link";
import { useAdults } from "@/lib/api/hooks";
import type { HomeData } from "@/lib/types";
import { DailyCircuitCard } from "../daily/DailyCircuitCard";
import { RaceCard } from "../race/RaceCard";
import { SumoCard } from "../sumo/SumoCard";
import { CurrencyPill } from "../ui/primitives";
import { ColonyVivarium } from "./ColonyVivarium";
import { ShioriBubble } from "./ShioriBubble";
import { TeamStrip } from "./TeamStrip";
import { TodoList } from "./TodoList";
import { WeekStrip } from "./WeekStrip";
import { DecorationEditor } from "./DecorationEditor";

const SLOT_GREETING = { morning: "おはよう", noon: "こんにちは", night: "こんばんは" } as const;

/** `hero` is shown right under the header (e.g. the "receive an egg" call to action when no week is running). */
export function HomeScreen({ data, hero, footer }: { data: HomeData; hero?: React.ReactNode; footer?: React.ReactNode }) {
  const adults = useAdults();
  const { clock, week, balances } = data;

  return (
    <div className="flex flex-col gap-4 px-4 pt-[max(14px,env(safe-area-inset-top))]">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-bold text-muted">{SLOT_GREETING[clock.slot]}</div>
          <h1 className="font-kiwi text-xl leading-tight">
            {week ? (
              <>
                <span className="tabular font-mono text-eye">{week.research_day}</span>日目
                <span className="ml-1.5 text-sm text-muted">（{clock.weekday_label}）</span>
              </>
            ) : (
              "ツユラボ"
            )}
          </h1>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <Link href="/settings" aria-label="通知の設定" className="min-h-11 inline-flex items-center rounded-lg p-2 text-sm text-muted focus-visible:outline-2 focus-visible:outline-leaf">設定</Link>
          <Link href="/care/sleep" className="inline-flex min-h-11 items-center px-2 text-sm text-muted">おやすみ</Link>
          <CurrencyPill kind="shizuku" value={balances.shizuku} />
        </div>
      </header>

      {week && <WeekStrip researchDay={week.research_day} />}

      {hero}

      {(data.fly || Boolean(adults.data?.length)) && <ColonyVivarium data={data} />}

      {week?.ready_to_eclose && (
        <Link
          href="/presentation"
          className="press glass-panel block rounded-xl p-5 focus-visible:outline-2 focus-visible:outline-banana"
        >
          <p className="text-xs font-bold tracking-widest text-banana">SUNDAY NIGHT</p>
          <h2 className="font-kiwi text-2xl">羽化の日へ</h2>
          <p className="mt-1 text-sm text-muted">この子と過ごした一週間。育ちを振り返って、羽化を見届けましょう。</p>
          <span className="mt-3 inline-flex items-center gap-1 min-h-11 rounded-lg border border-line px-4 py-2 text-sm font-medium">
            羽化の日をはじめる →
          </span>
        </Link>
      )}


      {data.shiori.memo && <ShioriBubble text={data.shiori.memo.text} evidence={data.shiori.memo.evidence} />}

      {data.todo.length > 0 && <TodoList todo={data.todo} />}
      <DailyCircuitCard />
      <RaceCard />
      <SumoCard />
      <Link href="/contest" className="rounded-2xl bg-tint-leaf p-4 text-center font-bold text-leaf">今週の見た目コンテストを見る →</Link>
      <TeamStrip team={data.team} />
      {week && data.fly && <details className="glass-panel rounded-lg p-3 text-sm"><summary>飼育棚の飾り</summary><div className="pt-3"><DecorationEditor stage={data.fly.stage} researchDay={week.research_day} moodLabel={data.fly.mood_label} night={clock.slot === "night"} /></div></details>}
      <details className="text-xs text-muted"><summary>飼育の経験</summary><CurrencyPill kind="research" value={balances.research_points} /></details>
      {footer}
    </div>
  );
}
