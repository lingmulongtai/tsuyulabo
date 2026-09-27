"use client";

import Link from "next/link";
import { useAcceptMating, useDeclineMating, useMatingInbox } from "@/lib/api/hooks-mating";
import type { components } from "@/lib/api/schema";
import { Button, Card, SectionTitle } from "../ui/primitives";
import { ErrorCard, QueryState } from "../ui/QueryState";

type Proposal = components["schemas"]["MatingView"];
const labels: Record<Proposal["status"], string> = { pending: "返事待ち", accepted: "承諾済み・卵が届きました", declined: "辞退済み", expired: "期限切れ" };

export function MatingInbox() {
  const inbox = useMatingInbox();
  return <section className="space-y-3" aria-label="お見合いの申込">
    <SectionTitle>お見合いのおたより</SectionTitle>
    <QueryState query={inbox}>{data => <>
      {data.incoming.length === 0 && data.outgoing.length === 0 && <Card className="p-4 text-sm text-muted">お見合いのおたよりはまだありません。フレンドの研究室で成虫を選んで申し込めます。</Card>}
      {data.incoming.map(proposal => <MatingMessage key={proposal.id} proposal={proposal} incoming />)}
      {data.outgoing.length > 0 && <details className="space-y-3"><summary className="cursor-pointer text-sm font-bold text-leaf">送ったおたより（{data.outgoing.length}件）</summary>{data.outgoing.map(proposal => <MatingMessage key={proposal.id} proposal={proposal} incoming={false} />)}</details>}
    </>}</QueryState>
  </section>;
}

export function MatingMessage({ proposal, incoming }: { proposal: Proposal; incoming: boolean }) {
  const accept = useAcceptMating();
  const decline = useDeclineMating();
  const pending = accept.isPending || decline.isPending;
  return <Card className="space-y-3 p-4">
    <h3 className="font-kiwi">{incoming ? `${proposal.proposer_name}さんから` : `${proposal.recipient_name}さんへ`}</h3>
    <p className="text-sm">{proposal.mother_name} ♀ × {proposal.father_name} ♂</p>
    <p role="status" className="text-sm text-leaf">{labels[proposal.status]}</p>
    {proposal.status === "pending" && <p className="text-xs text-muted">返事の期限：<time dateTime={proposal.expires_at}>{new Date(proposal.expires_at).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })}</time></p>}
    {incoming && proposal.status === "pending" && <>
      <p className="text-xs text-muted">承諾すると両方に卵が1個ずつ届き、両親の今週の交配枠を使います。育成中なら次の週まで保留できます。</p>
      <div className="flex gap-2"><Button block tone="leaf" disabled={pending} onClick={() => accept.mutate(proposal.id)}>{accept.isPending ? "承諾中…" : "承諾する"}</Button><Button block tone="plain" disabled={pending} onClick={() => decline.mutate(proposal.id)}>{decline.isPending ? "辞退中…" : "辞退する"}</Button></div>
    </>}
    {proposal.status === "accepted" && <Link href="/" className="block text-sm font-bold text-leaf">ホームで卵を選ぶ →</Link>}
    {accept.error && <ErrorCard error={accept.error} />}
    {decline.error && <ErrorCard error={decline.error} />}
  </Card>;
}
