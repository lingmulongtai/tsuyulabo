"use client";
import { useState } from "react";
import { useFriendLab, useGift, useInventory, useLike } from "@/lib/api/hooks";
import { cleanlinessState, hungerState } from "@/lib/raising-copy";
import { MATERIAL_LABELS } from "@/lib/display";
import { INGREDIENT_INFO } from "@/game/labels";
import { AdultCard } from "../collection/AdultCard";
import { Portrait } from "../vivarium/Portrait";
import { Button, Card, SectionTitle } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";
import { MatingProposal } from "./MatingProposal";

export function FriendLab({ id }: { id: string }) {
  const lab = useFriendLab(id);
  const inventory = useInventory();
  const like = useLike();
  const gift = useGift();
  const [material, setMaterial] = useState("banana");
  const [amount, setAmount] = useState(1);
  const available = inventory.data?.[material] ?? 0;
  return <QueryState query={lab}>{data => <>
    <h2 className="font-kiwi text-xl">{data.user.display_name}さんの飼育棚</h2>
    {data.week ? <><div className="mx-auto w-full max-w-xs"><Portrait stage={data.week.stage} seed={`friend-week-${id}`} label={`${data.user.display_name}さんが育てている子`} /></div><Card className="p-3 text-center text-sm text-muted">{hungerState(data.week.fly.hunger)} {cleanlinessState(data.week.fly.cleanliness)}</Card></> : <Card className="p-5 text-sm text-muted">今は育成をひとやすみしています。</Card>}
    <Button block tone="eye" disabled={like.isPending || like.isSuccess} onClick={() => like.mutate(id)}>{like.isSuccess ? "いいねしました ♥" : "いいね ♥"}</Button>
    {like.error && <ErrorCard error={like.error} retry={() => like.mutate(id)} />}
    <Card className="space-y-3 p-4"><h3 className="font-kiwi">材料をおすそわけ</h3><p className="text-xs text-muted">1日1回、5個まで。贈ると飼育の経験が10もらえます。</p>
      <QueryState query={inventory}>{() => <><label htmlFor="gift-material" className="block text-sm">材料</label>
        <select id="gift-material" value={material} disabled={gift.isPending} onChange={event => { setMaterial(event.target.value); setAmount(1); }} className="w-full rounded-xl border border-line bg-bg p-3">{Object.keys(INGREDIENT_INFO).map(key => <option key={key} value={key}>{MATERIAL_LABELS[key]}（{inventory.data?.[key] ?? 0}個）</option>)}</select>
        <label htmlFor="gift-amount" className="block text-sm">個数</label><select id="gift-amount" value={amount} disabled={gift.isPending} onChange={event => setAmount(Number(event.target.value))} className="w-full rounded-xl border border-line bg-bg p-3">{[1, 2, 3, 4, 5].map(n => <option key={n} value={n} disabled={n > available}>{n}個</option>)}</select>
        <Button block tone="banana" disabled={gift.isPending || gift.isSuccess || available < amount} onClick={() => gift.mutate({ friend_id: id, material, amount })}>{gift.isSuccess ? "おすそわけしました！" : "この材料を贈る"}</Button>
      </>}</QueryState>
      {gift.isSuccess && <p role="status" className="text-sm text-leaf">飼育の経験 +10。気持ちが届いたね。</p>}
    </Card>
    {gift.error && <ErrorCard error={gift.error} retry={() => gift.variables && gift.mutate(gift.variables)} />}
    <SectionTitle>コロニー</SectionTitle>{data.team.members.length === 0 && <p className="text-sm text-muted">まだコロニーを編成していません。</p>}
    {data.team.members.map(adult => <AdultCard key={adult.id} adult={adult} link={false} />)}
    <SectionTitle>育ったツユたち</SectionTitle>{data.adults.length === 0 && <p className="text-sm text-muted">最初の羽化を待っています。</p>}
    {data.adults.map(adult => <div key={adult.id} className="space-y-2"><AdultCard adult={adult} link={false} /><MatingProposal friendId={id} adultId={adult.id} /></div>)}
  </>}</QueryState>;
}
