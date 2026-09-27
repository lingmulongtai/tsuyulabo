import Link from "next/link";
import type { HomeData } from "@/lib/types";
import { Pupa } from "../art/Stages";
import { DailyCircuitCard } from "../daily/DailyCircuitCard";
import { RaceCard } from "../race/RaceCard";
import { SumoCard } from "../sumo/SumoCard";
import { CurrencyPill, Meter } from "../ui/primitives";
import { CircadianRing } from "../sleep/CircadianRing";
import { ActionGrid } from "./ActionGrid";
import { ShioriBubble } from "./ShioriBubble";
import { TeamStrip } from "./TeamStrip";
import { Terrarium } from "./Terrarium";
import { TodoList } from "./TodoList";
import { WeekStrip } from "./WeekStrip";

const SLOT_GREETING = { morning: "おはよう", noon: "こんにちは", night: "こんばんは" } as const;

/** `hero` is shown right under the header (e.g. the "receive an egg" call to action when no week is running). */
export function HomeScreen({ data, hero, footer }: { data: HomeData; hero?: React.ReactNode; footer?: React.ReactNode }) {
  const { clock, week, fly, balances } = data;
  const night = clock.slot === "night";

  return (
    <div className="flex flex-col gap-4 px-4 pt-[max(14px,env(safe-area-inset-top))]">
      <header className="flex flex-wrap items-center justify-between gap-2">
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
        <div className="flex shrink-0 items-center gap-1.5">
          <Link href="/settings" aria-label="通知の設定" className="rounded-full p-2 text-sm text-muted focus-visible:outline-2 focus-visible:outline-leaf">設定</Link>
          <Link href="/care/sleep" aria-label={`体内時計ゲージ ${data.circadian.gauge}、いっしょにねるへ`} className="rounded-full focus-visible:outline-2 focus-visible:outline-ai">
            <CircadianRing gauge={data.circadian.gauge} compact />
          </Link>
          <CurrencyPill kind="shizuku" value={balances.shizuku} />
          <CurrencyPill kind="research" value={balances.research_points} />
        </div>
      </header>

      {week && <WeekStrip researchDay={week.research_day} />}

      {hero}

      {week?.ready_to_eclose && (
        <Link
          href="/presentation"
          className="press relative block overflow-hidden rounded-[28px] bg-[radial-gradient(circle_at_80%_20%,#3b5f66,#10201d_70%)] p-5 text-white shadow-[0_0_36px_-10px_rgba(255,213,74,.8)] ring-2 ring-[#ffd54a]/70 focus-visible:outline-2 focus-visible:outline-banana"
        >
          <div className="absolute -right-3 -top-2 w-28 opacity-90 motion-safe:animate-pulse">
            <Pupa eyeShow={1} className="w-full" label="" />
          </div>
          <p className="text-xs font-bold tracking-widest text-[#ffd54a]">SUNDAY NIGHT</p>
          <h2 className="font-kiwi text-2xl">研究発表会へ</h2>
          <p className="mt-1 max-w-[62%] text-sm text-white/80">1週間の記録がそろいました。成果を振り返って、羽化を見届けよう。</p>
          <span className="mt-3 inline-flex items-center gap-1 rounded-full bg-[#ffd54a] px-4 py-1.5 text-sm font-bold text-[#3d2a05]">
            発表会をはじめる →
          </span>
        </Link>
      )}

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

      {data.todo.length > 0 && <ActionGrid todo={data.todo} />}
      {data.todo.length > 0 && <TodoList todo={data.todo} />}
      <DailyCircuitCard />
      <RaceCard />
      <SumoCard />
      <TeamStrip team={data.team} />
      {footer}
    </div>
  );
}
