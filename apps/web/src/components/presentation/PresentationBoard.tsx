"use client";

import type { WeekRank } from "@/game/expectation";
import { RANK_LABELS } from "../eclosion/traits";
import { ShioriBubble } from "../home/ShioriBubble";
import { Button, Card } from "../ui/primitives";

/** Mirrors GET /v1/weeks/current/presentation; scoring contracts remain unchanged. */
export interface PresentationData {
  meal_points: number;
  training_points: number;
  care_points: number;
  care_miss: number;
  penalty: number;
  points: number;
  rank: WeekRank;
  shizuku: number;
  research_points: number;
}

export function PresentationBoard({ data, hostLine, onNext }: {
  data: PresentationData; week?: number; hostLine?: string; onNext: () => void;
}) {
  const rows: Array<[string, number]> = [
    ["ごはん", data.meal_points], ["しつけ", data.training_points],
    ["お世話", data.care_points], ["世話ができなかった回数", data.care_miss],
    ["差し引き", -data.penalty], ["合計", data.points],
  ];
  return <div className="space-y-4">
    <Card className="space-y-4 p-5">
      <p className="text-xs tracking-widest text-muted">この子の一週間</p>
      <h2 className="font-kiwi text-2xl">もうすぐ、翅を広げる日。</h2>
      <p className="text-sm">卵から、ここまで育ちました。この子だけの姿を見届けましょう。</p>
      <ul className="space-y-3 text-sm text-muted">
        <li>{data.meal_points > 0 ? "配合したごはんを届けました。" : "ごはんを届けられない日もありました。"}</li>
        <li>{data.training_points > 0 ? "匂いとごほうびを結びつける練習をしました。" : "好き嫌いは、これからの楽しみです。"}</li>
        <li>{data.care_miss === 0 ? "毎日の世話を欠かさず続けました。" : "世話ができなかった日も含めて、この子の育ちです。"}</li>
      </ul>
      <div className="border-t border-line-soft pt-4">
        <p className="text-xs text-muted">育ちの評価</p>
        <p className="mt-1 font-kiwi text-xl text-banana">{RANK_LABELS[data.rank]}</p>
      </div>
      <details className="text-xs text-muted">
        <summary>育ちの評価の内訳</summary>
        <dl className="space-y-2 py-2">{rows.map(([label, value]) =>
          <div key={label} className="flex justify-between gap-3"><dt>{label}</dt><dd className="font-mono tabular">{value.toLocaleString("ja-JP")}</dd></div>)}</dl>
      </details>
    </Card>
    <ShioriBubble title="シオリからひとこと" text={hostLine ?? "ごはんやしつけ、毎日の世話が、この子の姿と個性につながります。羽化を見守りましょう。"} />
    <details className="glass-panel rounded-xl px-4 text-sm text-muted">
      <summary>受け取るもの</summary>
      <p className="pb-3">しずく +{Math.max(0, data.shizuku).toLocaleString("ja-JP")} ・ 飼育の経験 +{Math.max(0, data.research_points).toLocaleString("ja-JP")}</p>
    </details>
    <Button size="lg" block tone="banana" onClick={onNext}>羽化を見る</Button>
  </div>;
}
