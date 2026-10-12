/** Native disclosure keeps long evidence lists usable with keyboard and without JavaScript. */
export function EvidenceChips({ evidence, detail }: { evidence: string[]; detail?: string }) {
  const ids = [...new Set(evidence)];
  const chipClass = "rounded-md border border-line-soft px-1.5 font-mono text-[0.68rem] text-muted break-all";
  const chip = (id: string) => <span key={id} className={chipClass}>{id.includes("#") ? id : `#${id}`}</span>;
  if (!ids.length && !detail) return null;
  return <details aria-label="回答の根拠" className="mt-1 text-xs text-muted">
    <summary className="w-fit pr-4 focus-visible:outline-2">根拠</summary>
    {detail && <p className="mb-3 leading-relaxed">{detail}</p>}
    {ids.length > 0 && <p className="mb-2">この答えに使った飼育の記録と、コピーで試した記録です。</p>}
    <div className="flex flex-wrap gap-1">{ids.map(chip)}</div>
  </details>;
}
