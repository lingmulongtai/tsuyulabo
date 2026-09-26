import { TruthBadge } from "../ui/primitives";

/** Shiori's note. Every sentence she says carries record / experiment IDs; they are shown as chips. */
export function ShioriBubble({ text, evidence = [], title = "シオリの観察メモ" }: { text: string; evidence?: string[]; title?: string }) {
  return (
    <div className="flex gap-2.5">
      <div
        className="grid size-10 shrink-0 place-items-center rounded-full bg-ai font-kiwi text-lg text-white shadow-[0_3px_0_0_#3b2f93]"
        aria-hidden
      >
        シ
      </div>
      <div className="relative min-w-0 flex-1 rounded-2xl rounded-tl-md border border-line-soft bg-surface-2 px-3.5 py-2.5">
        <div className="mb-0.5 flex items-center gap-1.5 text-xs font-bold text-muted">
          {title}
          <TruthBadge kind="ai" />
        </div>
        <p className="text-sm leading-relaxed">{text}</p>
        {evidence.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {evidence.map((id) => (
              <span key={id} className="rounded-md bg-tint-ai px-1.5 font-mono text-[0.68rem] text-ai">
                #{id}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
