/** Native disclosure keeps long evidence lists usable with keyboard and without JavaScript. */
export function EvidenceChips({ evidence }: { evidence: string[] }) {
  const ids = [...new Set(evidence)];
  const chipClass = "rounded-md bg-tint-ai px-1.5 font-mono text-[0.68rem] text-ai";
  const chip = (id: string) => <span key={id} className={chipClass}>{id.startsWith("#") ? id : `#${id}`}</span>;
  if (!ids.length) return null;
  return <div aria-label="回答の根拠" className="mt-1.5 ml-14 flex flex-wrap items-start gap-1">
    {ids.slice(0, 6).map(chip)}
    {ids.length > 6 && <details>
      <summary className={`${chipClass} cursor-pointer list-none focus-visible:outline-2 focus-visible:outline-ai`} aria-label={`残り${ids.length - 6}件の根拠を表示・非表示`}>
        +{ids.length - 6}件
      </summary>
      <div className="mt-1 flex flex-wrap gap-1">{ids.slice(6).map(chip)}</div>
    </details>}
  </div>;
}
