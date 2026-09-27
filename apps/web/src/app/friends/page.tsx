"use client";
import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { DailyCircuitCard } from "@/components/daily/DailyCircuitCard";
import { CareFrame } from "@/components/games/CareFrame";
import { Button, Card, SectionTitle } from "@/components/ui/primitives";
import { ErrorCard, QueryState } from "@/components/ui/QueryState";
import { useAddFriend, useFriends, useMe, useNotifications, useRemoveFriend } from "@/lib/api/hooks";
import { notificationText } from "@/lib/display";

export default function FriendsPage() {
  const me = useMe();
  const friends = useFriends();
  const notifications = useNotifications();
  const add = useAddFriend();
  const remove = useRemoveFriend();
  const [code, setCode] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const [removing, setRemoving] = useState<string | null>(null);
  return <AppShell><CareFrame title="フレンドの研究室" subtitle="育ったツユを見せあおう">
    <DailyCircuitCard />
    <QueryState query={me}>{data => <Card className="space-y-3 p-5 text-center">
      <h2 className="font-kiwi">あなたのフレンドコード</h2><p className="select-all font-mono text-3xl tracking-widest">{data.friend_code}</p>
      <Button tone="leaf" size="sm" onClick={async () => { try { await navigator.clipboard.writeText(data.friend_code); setCopyMessage("コピーしました！"); } catch { setCopyMessage("コードを長押ししてコピーしてください。"); } }}>コードをコピー</Button>
      <p role="status" className="text-xs text-muted">{copyMessage}</p>
    </Card>}</QueryState>
    <Card className="p-4"><form className="space-y-3" onSubmit={event => { event.preventDefault(); if (code.length === 8 && !add.isPending) add.mutate(code, { onSuccess: () => setCode("") }); }}>
      <label htmlFor="friend-code" className="block text-sm font-bold">フレンドコードで追加</label>
      <input id="friend-code" autoComplete="off" autoCapitalize="characters" spellCheck={false} maxLength={8} pattern="[A-HJ-NP-Z2-9]{8}" value={code} onChange={event => setCode(event.target.value.toUpperCase().replace(/\s/g, ""))} placeholder="K7QX2MPA" className="w-full rounded-2xl border border-line bg-bg p-3 font-mono tracking-widest" />
      <Button block type="submit" disabled={add.isPending || !/^[A-HJ-NP-Z2-9]{8}$/.test(code)}>フレンドになる</Button>
    </form>{add.isSuccess && <p role="status" className="mt-3 text-sm text-leaf">フレンドになりました！</p>}</Card>
    {add.error && <ErrorCard error={add.error} />}
    <SectionTitle>フレンド</SectionTitle>
    <QueryState query={friends}>{data => <div className="space-y-3">{data.length === 0 && <Card className="p-5 text-sm text-muted">まだフレンドはいません。コードを交換してみよう。</Card>}
      {data.map(friend => <Card key={friend.id} className="space-y-2 p-4"><Link href={`/friends/${friend.id}`} className="flex items-center justify-between"><span><b>{friend.display_name}</b><span className="block text-xs text-muted">{friend.title || "研究仲間"}</span></span><span className="text-sm font-bold text-leaf">研究室へ →</span></Link>
        {removing === friend.id ? <div className="space-y-2 rounded-xl bg-bg p-3"><p className="text-xs">{friend.display_name}さんとのフレンド登録を解除しますか？</p><div className="flex gap-2"><Button size="sm" disabled={remove.isPending} onClick={() => remove.mutate(friend.id, { onSuccess: () => setRemoving(null) })}>解除する</Button><Button size="sm" tone="plain" onClick={() => setRemoving(null)}>やめる</Button></div></div> : <button className="text-xs text-muted underline" onClick={() => setRemoving(friend.id)}>登録を解除</button>}
      </Card>)}
    </div>}</QueryState>
    {remove.error && <ErrorCard error={remove.error} />}
    <SectionTitle>お知らせ</SectionTitle>
    <QueryState query={notifications}>{items => <Card className="divide-y divide-line-soft px-4">{items.length === 0 && <p className="py-4 text-sm text-muted">新しいお知らせはありません。</p>}{items.map(item => <div key={item.id} className="py-3"><p className="text-sm">{notificationText(item)}</p><time dateTime={item.created_at} className="text-xs text-muted">{new Date(item.created_at).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })}</time></div>)}</Card>}</QueryState>
  </CareFrame></AppShell>;
}
