import type { ShioriMood } from "../art/Shiori";
import { companionDisplay, raisingText } from "@/lib/raising-copy";
import { TruthBadge } from "../ui/primitives";
import { EvidenceChips } from "../shiori/EvidenceChips";

/** A quiet companion note with references behind a disclosure. */
export function ShioriBubble({ text, evidence = [], title = "シオリの観察メモ" }: {
  text: string;
  evidence?: string[];
  title?: string;
  mood?: ShioriMood;
}) {
  const display = companionDisplay(text, evidence);
  return <aside className="glass-panel rounded-xl px-4 py-3">
    <p className="mb-1 flex items-center gap-2 text-xs tracking-wide text-muted">{raisingText(title)} <TruthBadge kind="ai" /></p>
    <p className="text-sm leading-relaxed">{display.text}</p>
    <EvidenceChips evidence={evidence} detail={display.detail} />
  </aside>;
}
