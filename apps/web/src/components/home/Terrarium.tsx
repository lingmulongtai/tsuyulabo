import { FlyArt, STAGE_LABELS, type Stage } from "../art/FlyArt";
import type { Sex, Strain } from "../art/palette";
import { FlyAccessory } from "../art/decor/Accessories";
import { Ornament } from "../art/decor/Ornament";
import type { Layout } from "@/lib/api/hooks-contest";

export interface TerrariumProps {
  stage: Stage;
  researchDay: number;
  moodLabel?: string;
  strain?: Strain;
  sex?: Sex;
  night?: boolean;
  layout?: Layout;
}

/** The glass vial on its stage — the centre of the home screen. */
export function Terrarium({ stage, researchDay, moodLabel, strain, sex, night = false, layout }: TerrariumProps) {
  return (
    <div
      className="relative mx-auto aspect-[1/0.86] w-full overflow-hidden rounded-xl shadow-[inset_0_0_0_1px_rgba(30,44,41,0.08)]"
      style={{
        background: layout?.background === "rainbow_background"
          ? "radial-gradient(circle at 25% 20%, #e7bd78, #c3b396 48%, #827052 100%)"
          : night
          ? "radial-gradient(circle at 50% 38%, #5a462d 0%, #29251e 55%, #141310 100%)"
          : "radial-gradient(circle at 50% 38%, #eee6d8 0%, #c3b396 45%, var(--stage-glow) 100%)",
      }}
    >
      {/* floor glow */}
      <div className="absolute inset-x-[14%] bottom-[7%] h-[16%] rounded-[50%] bg-[radial-gradient(ellipse,rgba(231,189,120,0.18),transparent_70%)]" />

      {/* the vial */}
      <div className="absolute left-1/2 bottom-[8%] w-[58%] -translate-x-1/2 aspect-[1/1.02]">
        <div className={`absolute -top-[5%] -left-[7%] -right-[7%] h-[11%] rounded-[12px] border-2 z-10 ${layout?.vial === "rain_vial" ? "border-[#5d9caf] bg-gradient-to-b from-[#d8f3f4] to-[#8bc9d9]" : "border-[#c9bfa9] bg-gradient-to-b from-[#fbf7ee] to-[#e9e1cf]"}`} />
        <div className="absolute inset-0 rounded-b-[44%] border-[3px] border-t-0 border-[#a89a81]/90 bg-[linear-gradient(90deg,rgba(255,255,255,0.78),rgba(255,255,255,0.28)_40%,rgba(255,255,255,0.5))] overflow-hidden">
          <div className="absolute inset-x-0 bottom-0 h-[26%] bg-gradient-to-b from-[#f6da82] to-[#e0b04a]" />
          <div className="absolute left-[10%] top-[8%] h-[70%] w-[7%] rounded-full bg-white/70" />
        </div>
        <div className="absolute left-1/2 bottom-[3%] w-[86%] -translate-x-1/2">
          <FlyArt stage={stage} researchDay={researchDay} strain={strain} sex={sex} className="block h-auto w-full" />
          {stage === "adult" && <FlyAccessory item={layout?.accessory} />}
        </div>
      </div>
      <div className="absolute bottom-[7%] left-[12%] h-[15%] w-[15%]"><Ornament item={layout?.left} /></div>
      <div className="absolute bottom-[7%] right-[12%] h-[15%] w-[15%]"><Ornament item={layout?.right} /></div>

      {/* labels */}
      <div className="absolute left-3 top-3 flex flex-col gap-1.5">
        <span className="rounded-full bg-white/85 px-3 py-0.5 text-sm font-bold text-[#1e2c29] shadow-sm">{STAGE_LABELS[stage]}</span>
        {moodLabel && <span className="w-fit rounded-full bg-white/70 px-2.5 py-px text-xs font-bold text-[#655b4b]">{moodLabel}</span>}
      </div>
    </div>
  );
}
