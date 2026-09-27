"use client";

import Link from "next/link";
import { useDailyCircuit } from "@/lib/api/hooks-daily";

export function DailyCircuitCard() {
  const daily = useDailyCircuit();
  const status = daily.data?.my_result ? "今日はクリア済み" : daily.data?.attempt ? "本番は開始済み" : daily.data ? "今日はまだ未挑戦" : daily.error ? "状態を確認できません" : "確認中…";
  return <Link href="/daily" className="press flex items-center justify-between gap-3 rounded-3xl border border-line-soft bg-tint-ai p-4 focus-visible:outline-2 focus-visible:outline-ai">
    <span><span className="block font-kiwi text-lg text-ai">今日の回路</span><span className="text-xs text-muted">みんなで同じ問題に挑戦 · 毎朝4時更新</span></span>
    <span className="shrink-0 text-right text-xs font-bold text-ai"><span className="block">{status}</span><span aria-hidden>挑戦・順位を見る →</span></span>
  </Link>;
}
