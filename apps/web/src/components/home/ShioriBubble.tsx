import { Shiori, type ShioriMood } from "../art/Shiori";
import { TruthBadge } from "../ui/primitives";

/** Shiori's note. Every sentence she says carries record / experiment IDs; they are shown as chips. */
export function ShioriBubble({
  text,
  evidence = [],
  title = "シオリの観察メモ",
  mood = "normal",
}: {
  text: string;
  evidence?: string[];
  title?: string;
  mood?: ShioriMood;
}) {
  return (
    <div className="flex gap-2.5">
      <div className="size-11 shrink-0 overflow-hidden rounded-full bg-tint-ai ring-2 ring-[#5f4fcf]/60">
        <Shiori mood={mood} className="size-full" label="" />
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
