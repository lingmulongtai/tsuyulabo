"use client";

import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { QueryState } from "@/components/ui/QueryState";
import { TruthBadge } from "@/components/ui/primitives";
import { api, unwrap } from "@/lib/api/client";
import { useApiQuery } from "@/lib/api/query";
import { BrainPlayback } from "./BrainPlayback";
import { SCENARIOS, type BrainActivity, type Scenario } from "./types";

function useBrainActivity(flyId: string, scenario: Scenario) {
  return useApiQuery(["brain-activity", flyId, scenario], (signal) =>
    unwrap(
      api.GET("/v1/flies/{fly_id}/brain/activity", { signal, params: { path: { fly_id: flyId }, query: { scenario } } }),
    ).then((data) => data as unknown as BrainActivity),
  );
}

function Observation({ flyId, scenario }: { flyId: string; scenario: Scenario }) {
  const query = useBrainActivity(flyId, scenario);
  return <QueryState query={query}>{(data) => <BrainPlayback activity={data} />}</QueryState>;
}

export function BrainScreen({ flyId }: { flyId: string }) {
  const [scenario, setScenario] = useState<Scenario>("sugar");
  return <AppShell hideTabs>
    <div className="space-y-4 px-4 py-5">
      <Link href={`/adults/${encodeURIComponent(flyId)}`} className="text-sm text-leaf">← この子のページ</Link>
      <header className="space-y-2">
        <h1 className="font-kiwi text-2xl">この子の反応</h1>
        <p className="text-sm text-muted">ごはんや匂い、光への反応には、生まれつきの個性と育て方が表れます。</p>
        <p className="text-xs text-muted"><TruthBadge kind="real" /> 細胞名は実物から　<TruthBadge kind="model" /> ゲームの育ちのしくみ</p>
      </header>
      <label htmlFor="brain-scenario" className="block text-sm font-bold">何をしてみる？</label>
      <select id="brain-scenario" value={scenario} onChange={(event) => setScenario(event.target.value as Scenario)} className="w-full rounded-2xl border border-line bg-surface-2 p-3 text-sm">
        {Object.entries(SCENARIOS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
      {(scenario === "liked_odor" || scenario === "disliked_odor") && <p className="text-xs text-muted">どちらも同じバナナの匂いを出します。好き・苦手は、この子が学んだ重みで決まります。</p>}
      <Observation key={`${flyId}:${scenario}`} flyId={flyId} scenario={scenario} />
    </div>
  </AppShell>;
}
