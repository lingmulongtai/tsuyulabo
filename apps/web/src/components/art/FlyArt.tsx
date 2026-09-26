import type { Sex, Strain } from "./palette";
import { Egg, Larva, Pupa } from "./Stages";
import { Tsuyu } from "./Tsuyu";

export type Stage = "egg" | "larva1" | "larva2" | "larva3" | "wandering" | "pupa" | "adult";

export const STAGE_LABELS: Record<Stage, string> = {
  egg: "卵",
  larva1: "1齢幼虫",
  larva2: "2齢幼虫",
  larva3: "3齢幼虫",
  wandering: "さまよう幼虫",
  pupa: "さなぎ",
  adult: "成虫",
};

export interface FlyArtProps {
  stage: Stage;
  strain?: Strain;
  sex?: Sex;
  /** Research day 1–7; used for the pre-eclosion eye colour on the pupa. */
  researchDay?: number;
  animated?: boolean;
  className?: string;
}

/** Picks the right drawing for a growth stage. */
export function FlyArt({ stage, strain, sex, researchDay = 1, animated = true, className }: FlyArtProps) {
  const label = STAGE_LABELS[stage];
  switch (stage) {
    case "egg":
      return <Egg className={className} label={label} />;
    case "larva1":
      return <Larva instar={1} className={className} label={label} />;
    case "larva2":
      return <Larva instar={2} className={className} label={label} />;
    case "larva3":
      return <Larva instar={3} className={className} label={label} />;
    case "wandering":
      return <Larva instar={3} wandering className={className} label={label} />;
    case "pupa":
      return <Pupa eyeShow={researchDay >= 7 ? 1 : 0.35} className={className} label={label} />;
    case "adult":
      return <Tsuyu strain={strain} sex={sex} animated={animated} className={className} label={label} />;
  }
}
