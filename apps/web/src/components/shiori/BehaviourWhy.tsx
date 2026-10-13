"use client";
import { ShioriBubble } from "../home/ShioriBubble";
import { ErrorCard } from "../ui/QueryState";
import { useWhy } from "./hooks";
import type { components } from "@/lib/api/schema";
import type { Behaviour } from "../vivarium/types";

export function BehaviourWhy({ flyId, behaviour, source = "brain_decoder", onClose }: { flyId: string; behaviour: Behaviour; source?: components["schemas"]["WhyRequest"]["source"]; onClose: () => void }) {
  const why = useWhy();
  const supported = ["rest", "walk", "feed", "groom", "approach", "avoid", "escape", "turn_left", "turn_right", "fly"].includes(behaviour);
  const send = () => why.mutate({ fly_id: flyId, behaviour: supported ? behaviour as components["schemas"]["WhyRequest"]["behaviour"] : null, source });
  return <div className="glass-panel space-y-2 rounded-lg p-3">
    <div className="flex justify-between"><button type="button" className="min-h-11 px-3 text-sm" disabled={why.isPending || !supported} onClick={send}>{why.isPending ? "育ちの記録を確かめています…" : "どうして？"}</button><button type="button" className="min-h-11 px-3 text-xs text-muted" onClick={onClose}>閉じる</button></div>
    {why.data && <><ShioriBubble title="いまの動き" text={why.data.text} evidence={why.data.evidence} /><p className="text-xs text-muted">{why.data.disclaimer}</p></>}
    {why.error && <ErrorCard error={why.error} retry={send} />}
  </div>;
}
