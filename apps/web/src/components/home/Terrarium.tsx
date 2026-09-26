import { FlyArt, STAGE_LABELS, type Stage } from "../art/FlyArt";
import type { Sex, Strain } from "../art/palette";

export interface TerrariumProps {
  stage: Stage;
  researchDay: number;
  moodLabel?: string;
  strain?: Strain;
  sex?: Sex;
  night?: boolean;
}

const SPARKS: Array<[number, number, number]> = [
  [14, 18, 0],
  [82, 14, 0.8],
  [88, 58, 1.6],
  [10, 62, 1.1],
];

/** The glass vial on its stage — the centre of the home screen. */
export function Terrarium({ stage, researchDay, moodLabel, strain, sex, night = false }: TerrariumProps) {
  return (
    <div
      className="relative mx-auto aspect-[1/0.86] w-full overflow-hidden rounded-[32px] shadow-[inset_0_0_0_1px_rgba(30,44,41,0.08)]"
      style={{
        background: night
          ? "radial-gradient(circle at 50% 38%, #3b5f66 0%, #1d3538 55%, #10201d 100%)"
          : "radial-gradient(circle at 50% 38%, #ffffff 0%, #e4f4ef 45%, var(--stage-glow) 100%)",
      }}
    >
      {/* sparkles */}
      {SPARKS.map(([x, y, d]) => (
        <span
          key={`${x}-${y}`}
          className="absolute size-3 text-white/90 motion-safe:animate-pulse"
          style={{ left: `${x}%`, top: `${y}%`, animationDelay: `${d}s` }}
          aria-hidden
        >
          <svg viewBox="0 0 20 20">
            <path d="M10 0C11 7 13 9 20 10C13 11 11 13 10 20C9 13 7 11 0 10C7 9 9 7 10 0Z" fill="currentColor" />
          </svg>
        </span>
      ))}

      {/* floor glow */}
      <div className="absolute inset-x-[14%] bottom-[7%] h-[16%] rounded-[50%] bg-[radial-gradient(ellipse,rgba(31,133,121,0.22),transparent_70%)]" />

      {/* the vial */}
      <div className="absolute left-1/2 bottom-[8%] w-[58%] -translate-x-1/2 aspect-[1/1.02]">
        <div className="absolute -top-[5%] -left-[7%] -right-[7%] h-[11%] rounded-[12px] border-2 border-[#c9bfa9] bg-gradient-to-b from-[#fbf7ee] to-[#e9e1cf] z-10" />
        <div className="absolute inset-0 rounded-b-[44%] border-[3px] border-t-0 border-[#9dbbb4]/90 bg-[linear-gradient(90deg,rgba(255,255,255,0.78),rgba(255,255,255,0.28)_40%,rgba(255,255,255,0.5))] overflow-hidden">
          <div className="absolute inset-x-0 bottom-0 h-[26%] bg-gradient-to-b from-[#f6da82] to-[#e0b04a]" />
          <div className="absolute left-[10%] top-[8%] h-[70%] w-[7%] rounded-full bg-white/70" />
        </div>
        <div className="absolute left-1/2 bottom-[3%] w-[86%] -translate-x-1/2">
          <FlyArt stage={stage} researchDay={researchDay} strain={strain} sex={sex} className="block h-auto w-full" />
        </div>
      </div>

      {/* labels */}
      <div className="absolute left-3 top-3 flex flex-col gap-1.5">
        <span className="rounded-full bg-white/85 px-3 py-0.5 text-sm font-bold text-[#1e2c29] shadow-sm">{STAGE_LABELS[stage]}</span>
        {moodLabel && <span className="w-fit rounded-full bg-white/70 px-2.5 py-px text-xs font-bold text-[#1f8579]">{moodLabel}</span>}
      </div>
    </div>
  );
}
