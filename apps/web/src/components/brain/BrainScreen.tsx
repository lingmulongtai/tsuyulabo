"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { Button, TruthBadge } from "@/components/ui/primitives";
import { BrainPlayback } from "./BrainPlayback";
import { BrainConnection, readApi } from "./connection";
import { SCENARIOS, type BrainActivity, type Scenario } from "./types";

function Observation({ flyId, token, scenario }: { flyId: string; token: string; scenario: Scenario }) {
  const [data, setData] = useState<BrainActivity | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    readApi<BrainActivity>(`/v1/flies/${encodeURIComponent(flyId)}/brain/activity?scenario=${encodeURIComponent(scenario)}`, token, controller.signal)
      .then((result) => { if (!controller.signal.aborted) setData(result); })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "通信に失敗しました。");
      });
    return () => controller.abort();
  }, [flyId, token, scenario, attempt]);
  if (error) return <div role="alert" className="space-y-3 rounded-2xl bg-tint-eye p-4 text-sm">
    <p>{error}</p><Button tone="plain" size="sm" onClick={() => { setError(""); setAttempt(attempt + 1); }}>もう一度読み込む</Button>
  </div>;
  if (!data) return <p role="status" className="py-8 text-center text-sm text-muted">この子の脳を観察しています…</p>;
  return <BrainPlayback activity={data} />;
}

export function BrainScreen({ flyId }: { flyId: string }) {
  const [scenario, setScenario] = useState<Scenario>("sugar");
  return <AppShell hideTabs>
    <div className="space-y-4 px-4 py-5">
      <Link href={`/adults/${encodeURIComponent(flyId)}`} className="text-sm text-leaf">← この子のページ</Link>
      <header className="space-y-2">
        <h1 className="font-kiwi text-2xl">ツユの脳をのぞく</h1>
        <p className="text-sm text-muted">刺激が届いたら、どの細胞群が光るかな？</p>
        <p className="text-xs text-muted"><TruthBadge kind="real" /> 実在の細胞名　<TruthBadge kind="model" /> 小さな脳の模型</p>
      </header>
      <label htmlFor="brain-scenario" className="block text-sm font-bold">何をしてみる？</label>
      <select id="brain-scenario" value={scenario} onChange={(event) => setScenario(event.target.value as Scenario)} className="w-full rounded-2xl border border-line bg-surface-2 p-3 text-sm">
        {Object.entries(SCENARIOS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
      {(scenario === "liked_odor" || scenario === "disliked_odor") && <p className="text-xs text-muted">どちらも同じバナナの匂いを出します。好き・苦手は、この子が学んだ重みで決まります。</p>}
      <BrainConnection>{(token) => <Observation key={`${flyId}:${scenario}:${token}`} flyId={flyId} token={token} scenario={scenario} />}</BrainConnection>
    </div>
  </AppShell>;
}
