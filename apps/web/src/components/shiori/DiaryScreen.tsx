"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { QueryState } from "../ui/QueryState";
import { Card, TruthBadge } from "../ui/primitives";
import { EvidenceChips } from "./EvidenceChips";
import { AskShiori } from "./AskShiori";
import { DiaryMoment } from "./DiaryMoment";
import { ShareCard } from "./ShareCard";
import { useDiary, useIndividuals } from "./hooks";
import { raisingText } from "@/lib/raising-copy";

export function diaryText(text: string) { return raisingText(text.replace(/#[A-Za-z0-9][A-Za-z0-9_-]*/g, "").replace(/ +。/g, "。")); }

export function DiaryScreen() {
  const params = useSearchParams();
  const [selected, setSelected] = useState(params.get("fly") ?? "");
  const [momentId, setMomentId] = useState<string | null>();
  const individuals = useIndividuals();
  const flyId = selected || individuals.data?.[0]?.id || "";
  const diary = useDiary(flyId);
  const name = individuals.data?.find(fly => fly.id === flyId)?.name ?? "この子";
  return <div className="space-y-4">
    <QueryState query={individuals}>{flies => flies.length ? <label className="block text-sm">日記を読む子
      <select className="mt-2 block min-h-11 w-full rounded-lg border border-line bg-bg p-2" value={flyId} onChange={event => setSelected(event.target.value)}>
        {flies.map(fly => <option key={fly.id} value={fly.id}>{fly.name}</option>)}
      </select>
    </label> : <p className="text-sm text-muted">卵を迎えると、この子との日記が始まります。</p>}</QueryState>
    {flyId && <QueryState query={diary}>{entries => entries.length ? <ol className="space-y-4">{entries.map(entry => <li key={entry.id}>
      <Card className="space-y-3 p-4">
        <div className="flex items-center justify-between"><time dateTime={entry.day}>{entry.day}</time><TruthBadge kind="ai" /></div>
        {(momentId === undefined ? diary.data?.[0]?.id === entry.id : momentId === entry.id) ? <>
          <DiaryMoment moment={entry.snapshot} /><button className="min-h-11 text-xs text-muted" onClick={() => setMomentId(null)}>動きを閉じる</button>
        </> : <button className="min-h-11 text-xs text-muted" onClick={() => setMomentId(entry.id)}>この日の動きを見る</button>}
        <p className="text-sm leading-relaxed">{diaryText(entry.text)}</p>
        <EvidenceChips evidence={entry.evidence} detail={entry.text} />
        <ShareCard entry={entry} name={name} />
      </Card>
    </li>)}</ol> : <p className="text-sm text-muted">日記は毎晩まとめます。記録が残った日から、この子の育ちを読み返せます。</p>}</QueryState>}
    <details className="glass-panel rounded-lg p-3"><summary className="text-sm">気になることをシオリに聞く</summary><div className="pt-3"><AskShiori key={flyId} flyId={flyId || undefined} /></div></details>
  </div>;
}
