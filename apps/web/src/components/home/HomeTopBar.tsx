"use client";
import Link from "next/link";
import type { HomeData } from "@/lib/types";
import { DropIcon, MoonIcon } from "../ui/icons";
import glass from "../ui/material.module.css";
import motion from "../ui/motion.module.css";
import { WeekStrip } from "./WeekStrip";

const SLOTS = { morning: "朝", noon: "昼", night: "夜" } as const;
export function HomeTopBar({ data }: { data: HomeData }) {
  return <header className={`${glass.glass} ${motion.enter} absolute inset-x-3 top-[max(12px,env(safe-area-inset-top))] z-20 rounded-2xl px-4 py-2`}>
    <div className="flex items-center justify-between gap-2">
      <div className="min-w-0">
        <h1 className="text-sm font-medium">{data.week ? `${data.week.research_day}日目（${data.clock.weekday_label}）` : "ツユラボ"}</h1>
        <p className="text-[11px] text-[#d5cab4]">{SLOTS[data.clock.slot]} ・ 小さな命を見守る</p>
      </div>
      <div className="flex shrink-0 items-center">
        <Link href="/care/sleep" aria-label="おやすみ" className="grid size-11 place-items-center"><MoonIcon size={19} /></Link>
        <Link href="/settings" aria-label="通知の設定" className="grid size-11 place-items-center">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m10 3-1 3-3 1-3 3 2 2-1 4 3 2 3-1 2 4 3-2 1-3 4-1-1-4-3-1-1-3Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.3" /></svg>
        </Link>
        <span className="flex items-center gap-1 text-xs" aria-label={`しずく ${data.balances.shizuku}`}><DropIcon size={17} /><span className="tabular font-mono">{data.balances.shizuku.toLocaleString("ja-JP")}</span></span>
      </div>
    </div>
    {data.week && <WeekStrip researchDay={data.week.research_day} />}
  </header>;
}
