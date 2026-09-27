"use client";

import { usePendingEggs } from "@/lib/api/hooks-mating";
import { Button } from "../ui/primitives";
import { QueryState } from "../ui/QueryState";

export function PendingEggChoices({ pending, onStart }: { pending: boolean; onStart: (id: string) => void }) {
  const eggs = usePendingEggs();
  return <QueryState query={eggs}>{items => items.length > 0 && <section className="space-y-3 border-t border-line pt-4" aria-label="お見合いの卵">
    <h3 className="font-kiwi">届いているお見合いの卵</h3>
    <p className="text-xs text-muted">育てたい卵を選んでね。性別や見た目は羽化までのお楽しみ。ほかの卵は次の週にも選べます。</p>
    {items.map((egg, index) => <div key={egg.id} className="space-y-2 rounded-2xl bg-tint-leaf p-3">
      <p className="text-sm">{egg.mother_name} ♀ × {egg.father_name} ♂</p>
      <p className="text-xs text-muted">{new Date(egg.created_at).toLocaleDateString("ja-JP", { timeZone: "Asia/Tokyo" })} に届いた卵</p>
      <Button block tone="leaf" disabled={pending} onClick={() => onStart(egg.id)} aria-label={`${egg.mother_name}と${egg.father_name}のお見合いの卵 ${index + 1} を育てる`}>この卵で一週間をはじめる</Button>
    </div>)}
  </section>}</QueryState>;
}
