"use client";

import { useState } from "react";
import Link from "next/link";
import { Terrarium } from "../home/Terrarium";
import { Button, Card } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";
import type { Sex, Strain } from "../art/palette";
import { useAdults } from "@/lib/api/hooks-collection";
import {
  useCurrentContest, useContestResults, useEnterContest, useVoteContest,
  type ContestEntry, type CurrentContest, type ContestResults,
} from "@/lib/api/hooks-contest";

function Preview({ entry }: { entry: ContestEntry }) {
  return <div className="w-32 shrink-0"><Terrarium stage="adult" researchDay={7} strain={entry.strain as Strain} sex={entry.sex as Sex} layout={entry.layout} /></div>;
}

export function ContestScreen() {
  const current = useCurrentContest();
  const adults = useAdults();
  const results = useContestResults();
  const enter = useEnterContest();
  const vote = useVoteContest();
  const [adultId, setAdultId] = useState("");
  return <div className="space-y-4 px-4 py-6">
    <header><Link href="/" className="text-sm font-bold text-leaf">← 飼育室</Link><h1 className="mt-2 font-kiwi text-2xl">見た目コンテスト</h1></header>
    <QueryState query={current}>{data => <>
      <Card className="space-y-2 bg-tint-leaf p-5">
        <p className="text-xs font-bold text-leaf">{data.week} のお題</p>
        <h2 className="font-kiwi text-xl">{data.theme}</h2>
        <p className="text-sm text-muted">飾った飼育室と自慢の1匹を出そう。フレンドの投票で決まります。</p>
        <p className="text-xs text-muted">応募締切：{new Date(data.entry_close).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })}　投票終了：{new Date(data.vote_close).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })}</p>
      </Card>
      <MyEntry data={data} adults={adults.data ?? []} adultId={adultId} setAdultId={setAdultId} submit={id => enter.mutate(id)} pending={enter.isPending} />
      {enter.error && <ErrorCard error={enter.error} retry={() => enter.mutate(adultId)} />}
      <Card className="space-y-3 p-4"><h2 className="font-kiwi text-lg">フレンドの応募</h2>
        <p className="text-sm text-muted">{data.phase === "entry" ? "土曜日から投票できます。" : `残り ${data.votes_left} 票。同じ応募には1票まで。`}</p>
        {data.friends.length === 0 && <p className="text-sm text-muted">まだフレンドの応募はありません。</p>}
        {data.friends.map(entry => <div key={entry.id} className="flex items-center gap-3 border-t border-line-soft py-3">
          <Preview entry={entry} /><div className="min-w-0 flex-1"><b>{entry.display_name}</b><p className="text-sm text-muted">{entry.adult_name}</p>
          {data.phase === "vote" && <Button tone="leaf" size="sm" disabled={data.votes_left === 0 || vote.isPending || data.voted_entry_ids.includes(entry.id)} onClick={() => vote.mutate(entry.id)}>{data.voted_entry_ids.includes(entry.id) ? "投票済み" : "この飼育室に投票"}</Button>}</div>
        </div>)}
        {vote.error && <ErrorCard error={vote.error} />}
      </Card>
    </>}</QueryState>
    <QueryState query={results}>{data => <Podium data={data} />}</QueryState>
  </div>;
}

function MyEntry({ data, adults, adultId, setAdultId, submit, pending }: {
  data: CurrentContest; adults: { id: string; name: string }[];
  adultId: string; setAdultId: (id: string) => void; submit: (id: string) => void; pending: boolean;
}) {
  const selected = adultId || adults[0]?.id || "";
  return <Card className="space-y-3 p-4"><h2 className="font-kiwi text-lg">わたしの応募</h2>
    {data.my_entry ? <div className="flex items-center gap-3"><Preview entry={data.my_entry} /><p className="text-sm">{data.my_entry.adult_name}と応募しました。参加賞の5しずくを受け取りました。</p></div> : data.phase === "entry" ? <>
      <p className="text-sm text-muted">飼育室の今の飾りつけを応募に保存します。</p>
      {adults.length ? <><label className="block text-sm font-bold">自慢の1匹<select className="mt-1 w-full rounded-xl border border-line bg-surface-2 p-2" value={selected} onChange={event => setAdultId(event.target.value)}>{adults.map(adult => <option key={adult.id} value={adult.id}>{adult.name}</option>)}</select></label><Button tone="leaf" block disabled={pending} onClick={() => { if (selected) submit(selected); }}>この飼育室で応募する</Button></> : <p className="text-sm text-muted">成虫が育ったら応募できます。</p>}
    </> : <p className="text-sm text-muted">今週の応募は終了しました。</p>}
  </Card>;
}

function Podium({ data }: { data: ContestResults }) {
  const winners = [data.entries[1], data.entries[0], data.entries[2]].filter(Boolean);
  return <Card className="space-y-3 p-4"><h2 className="font-kiwi text-lg">結果 · {data.week}</h2>
    {data.entries.length === 0 && <p className="text-sm text-muted">結果はまだありません。</p>}
    <div className="flex items-end justify-center gap-2" aria-label="上位3位">
      {winners.map(entry => <div key={entry.id} className={`min-w-0 flex-1 rounded-t-2xl p-2 text-center ${entry.rank === 1 ? "bg-[#fff1bc] pb-7" : entry.rank === 2 ? "bg-[#e7eeec] pb-4" : "bg-[#f4dfcb] pb-2"}`}>
        <span className="font-kiwi text-lg">{entry.rank === 1 ? "🥇" : entry.rank === 2 ? "🥈" : "🥉"} {entry.rank}位</span>
        <div className="mx-auto max-w-32"><Terrarium stage="adult" researchDay={7} strain={entry.strain as Strain} sex={entry.sex as Sex} layout={entry.layout} /></div>
        <b className="block truncate text-sm">{entry.display_name}</b><span className="text-xs text-muted">{entry.votes}票</span>
      </div>)}
    </div>
    {data.entries.slice(3).map(entry => <div key={entry.id} className="flex justify-between border-t border-line-soft py-2 text-sm"><span>{entry.rank}位 · {entry.display_name}</span><span>{entry.votes}票</span></div>)}
  </Card>;
}
