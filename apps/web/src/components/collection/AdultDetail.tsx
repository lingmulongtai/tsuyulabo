"use client";
import { useState } from "react";
import { useAdult, useLevelUp, useRenameAdult } from "@/lib/api/hooks";
import { preferencePercent, SKILL_LABELS, SUBSKILL_LABELS, TRAIT_LABELS } from "@/lib/display";
import { CUE_INFO } from "@/game/labels";
import type { Cue } from "@/game/puzzles/types";
import { AdultBehavior } from "./AdultBehavior";
import { STRAIN_LABELS } from "../art/palette";
import { Button, Card, Meter, SectionTitle, Stars } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";
import { AskShiori } from "../shiori/AskShiori";

export function AdultDetail({ id }: { id: string }) {
  const adult = useAdult(id);
  const level = useLevelUp();
  const rename = useRenameAdult();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const trimmedName = name.trim();
  const validName = [...trimmedName].length >= 1 && [...trimmedName].length <= 12 && !/[\p{Cc}\p{Cf}\p{Cs}]/u.test(name);
  const [ask, setAsk] = useState(false);
  return <QueryState query={adult}>{data => <>
    <Card className="p-5 text-center"><AdultBehavior id={id} strain={data.strain} sex={data.sex} />
      <div className="flex items-center justify-center gap-2">
        <h2 className="font-kiwi text-2xl">{data.name} {data.sex === "f" ? "♀" : "♂"}</h2>
        <button type="button" aria-label="名前を変更" aria-expanded={editing} className="rounded-full border-2 border-line p-2 text-muted hover:bg-bg focus-visible:outline-2 focus-visible:outline-leaf" hidden={editing} onClick={() => { setName(data.name); rename.reset(); setEditing(true); }}>
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m16 3 5 5L8 21H3v-5L16 3Z M13 6l5 5" /></svg>
        </button>
      </div>
      {editing && <form className="my-3 space-y-2" onSubmit={event => {
        event.preventDefault();
        if (validName && !rename.isPending) rename.mutate({ id, name: trimmedName }, { onSuccess: () => setEditing(false) });
      }}>
        <label htmlFor="adult-name" className="block text-sm font-bold">新しい名前</label>
        <input id="adult-name" autoFocus value={name} disabled={rename.isPending} aria-describedby="adult-name-hint" aria-invalid={!validName} className="w-full rounded-2xl border-2 border-line bg-bg px-4 py-3 text-center focus:outline-leaf" onChange={event => setName(event.target.value)} onKeyDown={event => { if (event.key === "Escape" && !rename.isPending) setEditing(false); }} />
        <p id="adult-name-hint" className="text-xs text-muted">1〜12文字で名前をつけてね。制御文字は使えません。</p>
        <div className="flex justify-center gap-2">
          <Button type="submit" tone="banana" disabled={!validName || rename.isPending}>{rename.isPending ? "保存中…" : "保存する"}</Button>
          <Button type="button" disabled={rename.isPending} onClick={() => setEditing(false)}>キャンセル</Button>
        </div>
        {rename.error && <ErrorCard error={rename.error} />}
      </form>}
      {!editing && rename.isSuccess && <p role="status" className="mt-2 text-leaf">名前を変更しました！</p>}
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
