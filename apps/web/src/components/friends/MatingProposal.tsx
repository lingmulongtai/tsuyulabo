"use client";

import { useState } from "react";
import { useAdults } from "@/lib/api/hooks";
import { useMatingOptions, useProposeMating } from "@/lib/api/hooks-mating";
import type { components } from "@/lib/api/schema";
import { OffspringPrediction } from "../breeding/OffspringPrediction";
import { Button, Card } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";

export function MatingProposal({ friendId, adultId }: { friendId: string; adultId: string }) {
  const [open, setOpen] = useState(false);
  return <div className="space-y-2">
    <Button block tone="leaf" size="sm" onClick={() => setOpen(value => !value)} aria-expanded={open}>{open ? "お見合いを閉じる" : "お見合いを申し込む"}</Button>
    {open && <MatingPicker friendId={friendId} adultId={adultId} />}
  </div>;
}

function MatingPicker({ friendId, adultId }: { friendId: string; adultId: string }) {
  const options = useMatingOptions(friendId);
  const adults = useAdults();
  return <QueryState query={options}>{friends => {
    const friend = friends.find(adult => adult.id === adultId);
    if (!friend) return <p className="text-sm text-muted">この成虫は見つかりませんでした。</p>;
    return <QueryState query={adults}>{own => <MatingForm friendId={friendId} friend={friend} adults={own} />}</QueryState>;
  }}</QueryState>;
}

export function MatingForm({ friendId, friend, adults }: {
  friendId: string;
  friend: components["schemas"]["MatingOption"];
  adults: components["schemas"]["Adult"][];
}) {
  const [adultId, setAdultId] = useState("");
  const propose = useProposeMating();
  const candidates = adults.filter(adult => adult.sex !== friend.sex);
  const selected = candidates.find(adult => adult.id === adultId);
  if (propose.isSuccess) return <Card className="p-4"><p role="status" className="text-sm text-leaf">お見合いを申し込みました。フレンドの返事を待ってね。</p><p className="mt-2 text-xs text-muted">申込状況はフレンド画面で確認できます。</p></Card>;
  return <Card className="space-y-3 p-4">
    <h3 className="font-kiwi">{friend.name}のお相手を選ぶ</h3>
    <p className="text-xs text-muted">同じふたりの申込は週に1回、返事は48時間以内。承諾されると両方に卵が届き、両親は今週の交配をお休みします。育成中でも卵は保留できます。</p>
    {!friend.available && <p className="text-sm text-muted">この子は今週すでに交配しています。</p>}
    {candidates.length === 0 ? <p className="text-sm text-muted">お相手になる異性の成虫がまだいません。</p> : <label className="block text-sm font-bold">あなたの成虫
      <select className="mt-2 w-full rounded-xl border border-line bg-bg p-3" value={adultId} disabled={propose.isPending || !friend.available} onChange={event => { setAdultId(event.target.value); propose.reset(); }}>
        <option value="">選んでね</option>
        {candidates.map(adult => <option key={adult.id} value={adult.id}>{adult.name} {adult.sex === "f" ? "♀" : "♂"}</option>)}
      </select>
    </label>}
    {selected && <OffspringPrediction mother={selected.sex === "f" ? selected.genotype : friend.genotype} father={selected.sex === "m" ? selected.genotype : friend.genotype} />}
    <Button block tone="leaf" disabled={!selected || !friend.available || propose.isPending} onClick={() => { if (selected) propose.mutate({ friend_id: friendId, adult_id: selected.id, friend_adult_id: friend.id }); }}>{propose.isPending ? "申込中…" : "このふたりで申し込む"}</Button>
    {propose.error && <ErrorCard error={propose.error} />}
  </Card>;
}
