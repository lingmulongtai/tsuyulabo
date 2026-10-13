"use client";
import { ShioriBubble } from "../home/ShioriBubble";
import { useDismissHint, useHint } from "./hooks";

export function QuietHint({ flyId }: { flyId: string }) {
  const hint = useHint(flyId);
  const dismiss = useDismissHint();
  if (!hint.data) return null;
  return <div className="glass-panel rounded-lg p-2">
    <ShioriBubble title="この子のようす" text={hint.data.text} evidence={hint.data.evidence} />
    <button type="button" className="min-h-11 px-3 text-xs text-muted" disabled={dismiss.isPending} onClick={() => dismiss.mutate(hint.data!.id)}>今は閉じる</button>
    {dismiss.error && <p role="status" className="px-3 text-xs text-muted">閉じられませんでした。もう一度お試しください。</p>}
  </div>;
}
