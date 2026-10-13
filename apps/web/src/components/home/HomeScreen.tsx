"use client";
import Link from "next/link";
import { useAdults } from "@/lib/api/hooks";
import type { HomeData } from "@/lib/types";
import { DailyCircuitCard } from "../daily/DailyCircuitCard";
import { RaceCard } from "../race/RaceCard";
import { SumoCard } from "../sumo/SumoCard";
import { CurrencyPill } from "../ui/primitives";
import { ColonyVivarium } from "./ColonyVivarium";
import { HomeTopBar } from "./HomeTopBar";
import { TeamStrip } from "./TeamStrip";
import { DecorationEditor } from "./DecorationEditor";

export function HomeScreen({ data, hero, footer }: { data: HomeData; hero?: React.ReactNode; footer?: React.ReactNode }) {
  const adults = useAdults();
  const extras = <div className="space-y-3">
    {hero}
    <DailyCircuitCard /><RaceCard /><SumoCard />
    <Link href="/contest" className="block min-h-11 rounded-xl border border-line-soft p-3 text-center text-sm">今週の見た目コンテストを見る →</Link>
    <TeamStrip team={data.team} />
    {data.week && data.fly && <details className="text-sm"><summary>飼育棚の飾り</summary><DecorationEditor stage={data.fly.stage} researchDay={data.week.research_day} moodLabel={data.fly.mood_label} night={data.clock.slot === "night"} /></details>}
    <details className="text-xs text-muted"><summary>飼育の経験</summary><CurrencyPill kind="research" value={data.balances.research_points} /></details>
    <div className="grid gap-2">{footer}</div>
  </div>;
  const occupied = data.fly || Boolean(adults.data?.length);
  return <div className={occupied ? "fixed inset-0 overflow-hidden" : "relative mx-auto min-h-dvh max-w-xl px-4 pb-6 pt-32"}>
    {occupied ? <ColonyVivarium data={data}>{extras}</ColonyVivarium> : extras}
    <HomeTopBar data={data} />
  </div>;
}
