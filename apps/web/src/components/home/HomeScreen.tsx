import Link from "next/link";
import type { HomeData } from "@/lib/types";
import { Card, CurrencyPill, Meter } from "../ui/primitives";
import { ActionGrid } from "./ActionGrid";
import { ShioriBubble } from "./ShioriBubble";
import { TeamStrip } from "./TeamStrip";
import { Terrarium } from "./Terrarium";
import { TodoList } from "./TodoList";
import { WeekStrip } from "./WeekStrip";

const SLOT_GREETING = { morning: "おはよう", noon: "こんにちは", night: "こんばんは" } as const;

export function HomeScreen({ data, footer }: { data: HomeData; footer?: React.ReactNode }) {
  const { clock, week, fly, balances } = data;
  const night = clock.slot === "night";

  return (
    <div className="flex flex-col gap-4 px-4 pt-[max(14px,env(safe-area-inset-top))]">
      <header className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-bold text-muted">{SLOT_GREETING[clock.slot]}、研究員さん</div>
          <h1 className="font-kiwi text-xl leading-tight">
            {week ? (
              <>
                研究<span className="tabular font-mono text-eye">{week.research_day}</span>日目
                <span className="ml-1.5 text-sm text-muted">（{clock.weekday_label}）</span>
              </>
            ) : (
              "ツユラボ"
            )}
          </h1>
        </div>
        <div className="flex shrink-0 gap-1.5">
          <CurrencyPill kind="shizuku" value={balances.shizuku} />
          <CurrencyPill kind="research" value={balances.research_points} />
        </div>
      </header>

      {week && <WeekStrip researchDay={week.research_day} />}

      {week?.ready_to_eclose && <Link href="/presentation" className="press rounded-3xl focus-visible:outline-2 focus-visible:outline-banana">
        <Card className="border-banana bg-tint-banana p-5 text-center shadow-[0_0_28px_-8px_rgba(255,213,74,.7)]">
          <p className="mb-1 text-sm text-muted">1週間の記録がそろいました</p>
          <h2 className="font-kiwi text-xl">研究発表会へ</h2>
          <p className="mt-1 text-sm text-muted">今週の成果を振り返って、羽化を見届けよう。</p>
        </Card>
      </Link>}

      {week && fly ? (
        <Terrarium stage={fly.stage} researchDay={week.research_day} moodLabel={fly.mood_label} night={night} />
      ) : null}

      {fly && (fly.stage.startsWith("larva") || fly.stage === "wandering") && (
        <div className="grid grid-cols-3 gap-3 px-1">
          <Meter label="おなか" value={fly.hunger} color="linear-gradient(90deg,#f6c453,#e3ae35)" />
          <Meter label="きれい" value={fly.cleanliness} color="linear-gradient(90deg,#7fd0e6,#1f8579)" />
          <Meter label="ごきげん" value={fly.mood} color="linear-gradient(90deg,#ff9fb0,#d7263d)" hint={fly.mood_label} />
        </div>
      )}

      {data.shiori.memo && <ShioriBubble text={data.shiori.memo.text} evidence={data.shiori.memo.evidence} />}

      <ActionGrid todo={data.todo} />
      <TodoList todo={data.todo} />
      <TeamStrip team={data.team} />
      {footer}
    </div>
  );
}
