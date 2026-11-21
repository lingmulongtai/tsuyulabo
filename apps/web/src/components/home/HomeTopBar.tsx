"use client";
import Link from "next/link";
import type { HomeData } from "@/lib/types";
import { DropIcon, MoonIcon } from "../ui/icons";
import glass from "../ui/material.module.css";
import motion from "../ui/motion.module.css";
import { WeekStrip } from "./WeekStrip";

const SLOTS = { morning: "朝", noon: "昼", night: "夜" } as const;
export function HomeTopBar({ data }: { data: HomeData }) {
  return <header className={`${glass.glass} ${motion.enter} absolute inset-x-3 top-[max(12px,env(safe-area-inset-top))] z-20 rounded-xl px-4 py-2.5`}>
    <div className="flex items-center justify-between gap-2">
      <div className="min-w-0">
        <h1 className="text-sm font-medium text-ink">{data.week ? `${data.week.research_day}日目（${data.clock.weekday_label}）` : "ツユラボ"}</h1>
        <p className="text-xs text-muted">{SLOTS[data.clock.slot]} ・ 小さな命を見守る</p>
      </div>
      <div className="flex shrink-0 items-center gap-0.5">
        <Link href="/care/sleep" aria-label="おやすみ" className="grid size-11 place-items-center rounded-lg text-muted transition-colors hover:text-ink"><MoonIcon size={18} /></Link>
        <Link href="/settings" aria-label="通知の設定" className="grid size-11 place-items-center rounded-lg text-muted transition-colors hover:text-ink">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m10 3-1 3-3 1-3 3 2 2-1 4 3 2 3-1 2 4 3-2 1-3 4-1-1-4-3-1-1-3Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" /></svg>
        </Link>
        <span className="ml-1 flex items-center gap-1.5 rounded-lg border border-line-soft bg-surface-2 px-2.5 py-1 text-xs font-medium text-ink" aria-label={`しずく ${data.balances.shizuku}`}><DropIcon size={16} /><span className="tabular font-mono">{data.balances.shizuku.toLocaleString("ja-JP")}</span></span>
      </div>
    </div>
    {data.week && <WeekStrip researchDay={data.week.research_day} />}
  </header>;
}
