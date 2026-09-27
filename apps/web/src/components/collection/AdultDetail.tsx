"use client";
import { useState } from "react";
import { useAdult, useLevelUp } from "@/lib/api/hooks";
import { preferencePercent, SKILL_LABELS, SUBSKILL_LABELS, TRAIT_LABELS } from "@/lib/display";
import { CUE_INFO } from "@/game/labels";
import type { Cue } from "@/game/puzzles/types";
import { Tsuyu } from "../art/Tsuyu";
import { STRAIN_LABELS } from "../art/palette";
import { Button, Card, Meter, SectionTitle, Stars } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";
import { AskShiori } from "../shiori/AskShiori";

export function AdultDetail({ id }: { id: string }) {
  const adult = useAdult(id);
  const level = useLevelUp();
  const [ask, setAsk] = useState(false);
  return <QueryState query={adult}>{data => <>
    <Card className="p-5 text-center"><Tsuyu strain={data.strain} sex={data.sex} className="mx-auto h-56 w-64" label={data.name} />
      <h2 className="font-kiwi text-2xl">{data.name} {data.sex === "f" ? "♀" : "♂"}</h2>
      <p className="text-sm text-muted">{STRAIN_LABELS[data.strain].name} ・ {STRAIN_LABELS[data.strain].gene}</p><Stars value={data.stars} />
      <p className="my-3 font-mono text-xl">Lv.{data.level} / {data.level_cap}</p>
      <Meter label="げんき" value={data.energy} color="var(--leaf)" />
      <Button className="mt-4" tone="banana" disabled={level.isPending || data.level >= data.level_cap} onClick={() => level.mutate(id)}>{data.level >= data.level_cap ? "レベル上限" : `レベルアップ ・ ${20 * data.level}しずく`}</Button>
      {level.data && <p role="status" className="mt-2 text-leaf">Lv.{level.data.level}になりました！</p>}
    </Card>
    {level.error && <ErrorCard error={level.error} retry={() => level.mutate(id)} />}
    <SectionTitle>生まれつきの特性</SectionTitle>
    <Card className="flex flex-wrap gap-2 p-4">{data.traits.map(trait => <span key={trait} className="rounded-full bg-tint-leaf px-3 py-1 text-sm font-bold text-leaf">{TRAIT_LABELS[trait] ?? "新しい特性"}</span>)}</Card>
    <SectionTitle>サブスキル</SectionTitle>
    <Card className="space-y-2 p-4">{[10, 25, 50].map((unlock, index) => <p key={unlock} className={`rounded-xl p-2 text-sm ${data.subskills[index] ? "bg-tint-banana" : "bg-bg text-muted"}`}>Lv.{unlock} ・ {data.subskills[index] ? SUBSKILL_LABELS[data.subskills[index]] ?? "新しいスキル" : "まだひみつ"}</p>)}</Card>
    <SectionTitle>好き・苦手</SectionTitle>
    <Card className="space-y-4 p-4">{Object.entries(data.preferences).map(([cue, value]) => <div key={cue}>
      <Meter label={CUE_INFO[cue as Cue]?.name ?? "新しい合図"} value={preferencePercent(value)} hint={value > 0.1 ? "好き" : value < -0.1 ? "苦手" : "どちらでも"} color="linear-gradient(90deg,var(--ai),var(--leaf))" />
      <p className="flex justify-between text-[0.65rem] text-muted"><span>苦手 −1</span><span>0</span><span>好き +1</span></p>
    </div>)}{Object.keys(data.preferences).length === 0 && <p className="text-sm text-muted">まだ観察記録がありません。</p>}</Card>
    <SectionTitle>とくいワザ</SectionTitle>
    <Card className="p-4 text-sm">{Object.entries(data.skills).filter(([, active]) => active).map(([skill]) => <p key={skill} className="py-1 font-bold text-leaf">✦ {SKILL_LABELS[skill] ?? "新しいワザ"}</p>)}{!Object.values(data.skills).some(Boolean) && <p className="text-muted">まだ見つかっていません。</p>}</Card>
    <Button tone="ai" block aria-expanded={ask} onClick={() => setAsk(value => !value)}>なんで？ シオリに聞く</Button>
    {ask && <AskShiori context={`成虫「${data.name}」（個体ID: ${data.id}）について。`} initialQuestion="この子の好き・苦手は、どうしてこうなったの？" />}
  </>}</QueryState>;
}
