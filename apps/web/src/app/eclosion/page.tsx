"use client";

import { useState } from "react";
import { EclosionStage, type EclosionResult } from "@/components/eclosion/EclosionStage";
import { ODDS, demoEclosion } from "@/components/eclosion/demo";
import { RANK_LABELS, TIER_NAMES } from "@/components/eclosion/traits";
import { CareFrame } from "@/components/games/CareFrame";
import { AppShell } from "@/components/shell/AppShell";
import { Card } from "@/components/ui/primitives";

type Rank = keyof typeof ODDS;
const DOT = ["#FFFFFF", "#7FC8FF", "#FFD54A", "conic-gradient(#FF6B8B,#FFC857,#7EE0A1,#5EC8F2,#A78BFA,#FF6B8B)"];

export default function EclosionPage() {
  const [rank, setRank] = useState<Rank>("gold");
  const [result, setResult] = useState<EclosionResult | null>(null);
  const [run, setRun] = useState(0);

  return (
    <AppShell hideTabs>
      <CareFrame title="羽化" subtitle="1週間がんばったぶん、当たりやすくなる">
        <EclosionStage
          key={run}
          result={result}
          onStart={() => setResult(demoEclosion(rank))}
          onDone={() => {
            setResult(null);
            setRun((r) => r + 1);
          }}
          doneLabel="もう一度（デモ）"
        />

        <Card className="px-4 py-3">
          <div className="mb-2">
            <h2 className="mb-1.5 font-kiwi">今週のランク</h2>
            <div className="grid grid-cols-4 gap-1">
              {(Object.keys(ODDS) as Rank[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  aria-pressed={rank === r}
                  onClick={() => setRank(r)}
                  className={`whitespace-nowrap rounded-full py-1 text-xs font-bold ${rank === r ? "bg-ink text-bg" : "bg-bg text-muted"}`}
                >
                  {RANK_LABELS[r]}
                </button>
              ))}
            </div>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted">
                <th className="font-normal">予兆の色</th>
                <th className="font-normal">結果</th>
                <th className="text-right font-normal">確率</th>
              </tr>
            </thead>
            <tbody>
              {TIER_NAMES.map((name, i) => (
                <tr key={name} className="border-t border-line-soft">
                  <td className="py-1.5">
                    <span className="mr-2 inline-block size-3 rounded-full border border-line align-middle" style={{ background: DOT[i] }} />
                    {["白", "青", "金", "虹"][i]}
                  </td>
                  <td>{["素質 ★1〜2", "素質 ★3", "素質 ★4", "★5 ＋ めずらしい系統"][i]}</td>
                  <td className="text-right font-mono tabular">{ODDS[rank][i]}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-muted">確率はすべて公開しています。本番の羽化は1週間に1回で、お金で回すことはできません。</p>
        </Card>
      </CareFrame>
    </AppShell>
  );
}
