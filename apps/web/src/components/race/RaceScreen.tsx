"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Tsuyu } from "@/components/art/Tsuyu";
import { traitName } from "@/components/eclosion/traits";
import { CareFrame } from "@/components/games/CareFrame";
import { Button, Card, TruthBadge } from "@/components/ui/primitives";
import { ErrorCard, QueryState } from "@/components/ui/QueryState";
import { placeToken, raceScore, RACE_CUES, type MazeToken } from "@/game/maze-race";
import { useAdults } from "@/lib/api/hooks-collection";
import { useCurrentRace, useEnterRace, useRaceRanking, useRaceReplay, type CurrentRace } from "@/lib/api/hooks-race";
import type { components } from "@/lib/api/schema";
import { MazeBoard } from "./MazeBoard";
import { RacePlayback } from "./RacePlayback";

export function RaceScreen() {
  const race = useCurrentRace();
  const adults = useAdults();
  return <CareFrame title="迷路レース" subtitle="合図を置いたら、あとはツユの脳におまかせ。">
    <QueryState query={race}>{data => <QueryState query={adults}>{collection => <RaceSession key={data.week} race={data} adults={collection} />}</QueryState>}</QueryState>
  </CareFrame>;
}

function RaceSession({ race, adults }: { race: CurrentRace; adults: components["schemas"]["Adult"][] }) {
  const cache = useQueryClient();
  const enter = useEnterRace();
  const ranking = useRaceRanking(race.week);
  const [adultId, setAdultId] = useState(race.my_entry?.adult_id ?? adults[0]?.id ?? "");
  const [tokens, setTokens] = useState<MazeToken[]>(race.my_entry?.placements ?? []);
  const [cue, setCue] = useState<MazeToken["cue"]>("banana");
  const [message, setMessage] = useState("");
  const [viewId, setViewId] = useState("");
  const replayId = viewId || race.my_entry?.id || "";
  const replay = useRaceReplay(replayId);
  const status = replay.data?.entry.status;
  const replayAdult = adults.find(adult => adult.id === replay.data?.entry.adult_id);
  useEffect(() => {
    if (status === "succeeded" || status === "failed") {
      void cache.invalidateQueries({ queryKey: ["race"] });
      void cache.invalidateQueries({ queryKey: ["race-ranking"] });
    }
  }, [status, replayId, cache]);
  const submit = () => enter.mutate({ week: race.week, adult_id: adultId, placements: tokens }, {
    onSuccess: entry => { setViewId(entry.id); setMessage("エントリーしました。走りを計算しています。"); },
  });
  return <>
    <Card className="space-y-2 p-4">
      <div className="flex items-center justify-between"><b className="text-ai">今週のコース · {race.week}</b><TruthBadge kind="model" /></div>
      <p className="text-sm">しつけで覚えた好き・苦手と、生まれつきの特性が走りに出ます。</p>
      <p className="text-xs text-muted">締切：{new Date(race.deadline).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })}（日本時間）<br />再エントリーすると今週の記録を置き換えます。購入したものは結果に影響しません。</p>
    </Card>

    {adults.length === 0 ? <Card className="space-y-3 p-5 text-center"><Tsuyu className="mx-auto h-24 w-24" /><p>成虫が育ったらレースに参加できます。</p><Link className="font-bold text-leaf underline" href="/">飼育室で育てる →</Link></Card> : <>
      <h2 className="font-kiwi text-lg">1. 走るツユを選ぶ</h2>
      <p className="text-xs text-muted">好みのバー：左が苦手、真ん中が中立、右が好き。</p>
      <div className="flex gap-3 overflow-x-auto pb-2" role="group" aria-label="走る成虫">
        {adults.map(adult => <button key={adult.id} aria-pressed={adult.id === adultId} onClick={() => setAdultId(adult.id)} className={`w-56 shrink-0 rounded-3xl border-2 p-4 text-left ${adult.id === adultId ? "border-ai bg-tint-ai" : "border-line bg-surface-2"}`}>
          <div className="flex items-center gap-2"><Tsuyu strain={adult.strain} sex={adult.sex} className="h-14 w-14" /><div><b>{adult.name}</b><p className="text-xs text-muted">{adult.traits.map(traitName).join("・") || "個性を観察しよう"}</p></div></div>
          <div className="mt-2 space-y-2">{RACE_CUES.map(item => {
            const value = Math.max(-1, Math.min(1, adult.preferences[item.id] ?? 0));
            return <div key={item.id}><div className="flex justify-between text-xs"><span>{item.icon} {item.label}</span><span>{value > 0.1 ? "好き" : value < -0.1 ? "苦手" : "中立"}</span></div><div role="meter" aria-label={`${adult.name}の${item.label}の好み`} aria-valuemin={-1} aria-valuemax={1} aria-valuenow={value} className="relative mt-1 h-2 overflow-hidden rounded bg-line-soft"><div className="h-full bg-ai" style={{ width: `${(value + 1) * 50}%` }} /><span className="absolute inset-y-0 left-1/2 w-px bg-ink/60" /></div></div>;
          })}</div>
        </button>)}
      </div>
      <Card className="space-y-4 p-4">
        <div className="flex justify-between"><h2 className="font-kiwi text-lg">2. 合図で作戦を立てる</h2><b className="text-ai">{tokens.length} / 3</b></div>
        <p className="text-xs text-muted">合図を選んで通路をタップ。置いた合図をもう一度タップすると取り除けます。匂いは通路に沿って届きます。</p>
        <div className="flex flex-wrap gap-2" role="group" aria-label="置く合図">{RACE_CUES.map(item => <Button key={item.id} tone={item.id === cue ? "ai" : "plain"} size="sm" aria-pressed={item.id === cue} onClick={() => setCue(item.id)}>{item.icon} {item.label}</Button>)}</div>
        <MazeBoard maze={race.maze} tokens={tokens} onCell={(x, y) => {
          const next = placeToken(race.maze, tokens, { x, y, cue });
          setTokens(next.tokens); setMessage(next.message);
        }} />
        <p className="text-xs text-muted">出：スタート ／ 旗：ゴール ／ 暗いマス：壁</p>
        <div className="flex justify-end"><Button tone="plain" size="sm" disabled={!tokens.length} onClick={() => { setTokens([]); setMessage("合図をすべて取り除きました。"); }}>合図をクリア</Button></div>
      </Card>
      <p role="status" className="text-sm text-ai">{message}</p>
      <Button block tone="ai" size="lg" disabled={!adultId || enter.isPending} onClick={submit}>{enter.isPending ? "エントリー中…" : race.my_entry ? "作戦を変えて再エントリー" : "この作戦で走る"}</Button>
      {enter.error && <ErrorCard error={enter.error} retry={submit} />}
    </>}

    {replayId && <QueryState query={replay}>{data => <RacePlayback key={data.entry.id} replay={data} appearance={replayAdult} />}</QueryState>}
    {race.my_entry && replayId !== race.my_entry.id && <Button tone="plain" onClick={() => setViewId("")}>自分の走りに戻る</Button>}

    <Card className="space-y-3 p-4">
      <h2 className="font-kiwi text-lg">フレンドと今週の記録</h2>
      <p className="text-xs text-muted">ゴールした歩数で競います。未完走なら、残りの道のりが短い順。同点は同じ順位です。</p>
      <QueryState query={ranking}>{data => data.week === race.week ? <div className="divide-y divide-line-soft">
        {data.entries.length === 0 && <p className="py-4 text-sm text-muted">まだ記録がありません。最初の走りを残そう。</p>}
        {data.entries.map(entry => <button key={entry.entry_id} className="flex w-full items-center gap-3 py-3 text-left" onClick={() => setViewId(entry.entry_id)}>
          <b className="text-xl text-ai">{entry.rank}</b><span className="flex-1"><b className="text-sm">{entry.display_name}{entry.is_me ? "（あなた）" : ""}</b><span className="block text-xs text-muted">{raceScore(entry)}</span></span><span className="text-xs font-bold text-leaf">再生 →</span>
        </button>)}
      </div> : <p className="text-sm text-muted">新しい週の記録に切り替えています。</p>}</QueryState>
    </Card>
  </>;
}
