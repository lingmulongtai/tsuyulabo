"use client";
import { useState } from "react";
import { useAdvanceTime, useDevTime, useResetTime } from "@/lib/api/hooks";
import { Button } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";

export function DevTimePanel() {
  if (process.env.NEXT_PUBLIC_DEV_TOOLS !== "1") return null;
  return <EnabledPanel />;
}

function EnabledPanel() {
  const [open, setOpen] = useState(false);
  const time = useDevTime();
  const advance = useAdvanceTime();
  const reset = useResetTime();
  const busy = advance.isPending || reset.isPending;
  return <aside aria-label="開発用の時間操作" className="fixed bottom-24 right-3 z-40 max-w-[min(340px,calc(100vw-24px))] rounded-2xl border border-line bg-surface-2/95 p-3 shadow-xl backdrop-blur">
    <button className="w-full text-right text-xs font-bold text-ai" aria-expanded={open} onClick={() => setOpen(value => !value)}>開発用の時計 {open ? "−" : "＋"}</button>
    {open && <div className="mt-3 space-y-3"><QueryState query={time}>{data => <p className="text-xs" aria-live="polite">ゲーム時刻<br /><time>{typeof data.game_now === "string" ? new Date(data.game_now).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" }) : "—"}</time></p>}</QueryState>
      <div className="grid grid-cols-2 gap-2">{([["next_slot", "次の時間帯"], ["next_day", "次の日"], ["eclosion", "羽化の夜へ"]] as const).map(([to, label]) => <Button key={to} size="sm" tone="plain" disabled={busy} onClick={() => advance.mutate({ to })}>{label}</Button>)}
        <Button size="sm" tone="ai" disabled={busy} onClick={() => reset.mutate()}>時刻をリセット</Button>
      </div>
      <p className="text-xs text-muted">リセットは時計だけを戻します。育成記録は残ります。</p>
      {(advance.error || reset.error) && <ErrorCard error={advance.error ?? reset.error} />}
    </div>}
  </aside>;
}
