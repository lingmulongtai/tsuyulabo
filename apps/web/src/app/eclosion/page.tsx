"use client";

import { Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { EclosionStage, type EclosionResult } from "@/components/eclosion/EclosionStage";
import { ODDS, demoEclosion } from "@/components/eclosion/demo";
import { RANK_LABELS, TIER_NAMES } from "@/components/eclosion/traits";
import { CareFrame } from "@/components/games/CareFrame";
import { AppShell } from "@/components/shell/AppShell";
import { Card } from "@/components/ui/primitives";
import { ErrorCard, LoadingCard, QueryState } from "@/components/ui/QueryState";
import { useEclose, useOdds, usePresentation } from "@/lib/api/hooks";
import { eclosionOdds, eclosionResult, type EclosionOdds } from "@/lib/api/eclosion-display";

type Rank = keyof EclosionOdds;
const DOT = ["#FFFFFF", "#7FC8FF", "#FFD54A", "conic-gradient(#FF6B8B,#FFC857,#7EE0A1,#5EC8F2,#A78BFA,#FF6B8B)"];

function OddsTable({ odds, rank, onRank, demo = false }: { odds: EclosionOdds; rank: Rank; onRank: (rank: Rank) => void; demo?: boolean }) {
  return <Card className="px-4 py-3">
    <div className="mb-2">
      <h2 className="mb-1.5 font-kiwi">{demo ? "今週のランク" : "確率表のランク"}</h2>
      <div className="grid grid-cols-4 gap-1">
        {(Object.keys(odds) as Rank[]).map(r => <button key={r} type="button" aria-pressed={rank === r} onClick={() => onRank(r)}
          className={`whitespace-nowrap rounded-full py-1 text-xs font-bold ${rank === r ? "bg-ink text-bg" : "bg-bg text-muted"}`}>
          {RANK_LABELS[r]}
        </button>)}
      </div>
    </div>
    <table className="w-full text-sm">
      <thead><tr className="text-left text-xs text-muted">
        <th className="font-normal">予兆の色</th><th className="font-normal">結果</th><th className="text-right font-normal">確率</th>
      </tr></thead>
      <tbody>{TIER_NAMES.map((name, i) => <tr key={name} className="border-t border-line-soft">
        <td className="py-1.5"><span className="mr-2 inline-block size-3 rounded-full border border-line align-middle" style={{ background: DOT[i] }} />{["白", "青", "金", "虹"][i]}</td>
        <td>{["素質 ★1〜2", "素質 ★3", "素質 ★4", "★5 ＋ めずらしい系統"][i]}</td>
        <td className="text-right font-mono tabular">{odds[rank][i]}%</td>
      </tr>)}</tbody>
    </table>
    <p className="mt-2 text-xs text-muted">確率はすべて公開しています。本番の羽化は1週間に1回で、お金で回すことはできません。</p>
    {!demo && <p className="mt-2 text-xs text-muted">基本の確率です。温度あわせと場所えらびの結果により、ボーナスが加わります。</p>}
  </Card>;
}

function PublishedOdds({ initialRank }: { initialRank: Rank }) {
  const odds = useOdds();
  const [rank, setRank] = useState(initialRank);
  let table: EclosionOdds | undefined;
  let error: unknown;
  try { if (odds.data) table = eclosionOdds(odds.data); } catch (cause) { error = cause; }
  if (error) return <ErrorCard error={error} retry={() => void odds.refetch()} />;
  return <QueryState query={odds}>{() => table && <OddsTable odds={table} rank={rank} onRank={setRank} />}</QueryState>;
}

function LiveEclosion() {
  const router = useRouter();
  const presentation = usePresentation();
  const eclose = useEclose();
  const mapped = useMemo(() => {
    try { return { result: eclose.data ? eclosionResult(eclose.data) : null, error: null }; }
    catch (error) { return { result: null, error }; }
  }, [eclose.data]);
  const start = () => { if (!eclose.isPending && !eclose.data) eclose.mutate(); };
  return <QueryState query={{ ...presentation, error: eclose.data ? null : presentation.error }}>{data => <>
    <EclosionStage result={mapped.result} onStart={start} onDone={() => {
      if (eclose.data) router.push(`/adults/${encodeURIComponent(eclose.data.adult.id)}`);
    }} />
    {eclose.isPending && <p role="status" className="text-center text-sm text-muted">羽化を待っています…</p>}
    {!eclose.isPending && eclose.error && <ErrorCard error={eclose.error} retry={start} />}
    {mapped.error ? <ErrorCard error={mapped.error} /> : null}
    <PublishedOdds initialRank={data.rank} />
  </>}</QueryState>;
}

function DemoEclosion() {
  const [rank, setRank] = useState<Rank>("gold");
  const [result, setResult] = useState<EclosionResult | null>(null);
  const [run, setRun] = useState(0);
  return <>
    <EclosionStage key={run} result={result} onStart={() => setResult(demoEclosion(rank))} onDone={() => {
      setResult(null);
      setRun(value => value + 1);
    }} doneLabel="もう一度（デモ）" />
    <OddsTable odds={ODDS} rank={rank} onRank={setRank} demo />
  </>;
}

function EclosionSession() {
  const search = useSearchParams();
  return search.get("demo") === "1" ? <DemoEclosion /> : <LiveEclosion />;
}

export default function EclosionPage() {
  return <AppShell hideTabs><CareFrame title="羽化" subtitle="1週間がんばったぶん、当たりやすくなる">
    <Suspense fallback={<LoadingCard />}><EclosionSession /></Suspense>
  </CareFrame></AppShell>;
}
