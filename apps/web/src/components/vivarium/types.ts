/** API stages are accepted without exposing hidden genotypes before eclosion. */
export type Stage = "egg" | "larva" | "larva1" | "larva2" | "larva3" | "wandering" | "pupa" | "adult";
export type Behaviour = "rest" | "walk" | "turn_left" | "turn_right" | "feed" | "escape" | "groom" | "approach" | "avoid" | "fly" | "stop" | "flee" | "burrow";
export type Phenotype = "wild" | "white" | "yellow" | "ebony" | "curly" | "vestigial";
export type Quality = "high" | "medium" | "low";
export type Point = readonly [number, number, number];
export interface Habitat {
  /** Normalized 0..1, not percent. */
  humidity?: number;
  food?: { color?: string; moisture?: number; yeast?: number };
  mould?: number;
  grime?: number;
  /** Normalized development within the pupal stage. */
  pupaAge?: number;
}
export interface VivariumHandle {
  setBehaviour(behaviour: Behaviour): void;
  /** World coordinates; y is up, food surface is y = -1.08. */
  pointOfInterest(point: Point): void;
}
export interface VivariumProps {
  stage?: Stage;
  behaviour?: Behaviour;
  environment?: Habitat;
  quality?: Quality | "auto";
  sex?: "f" | "m";
  traits?: readonly Phenotype[];
  /** Stable individual ID controls variation; never used for genetics. */
  seed?: string;
  pointOfInterest?: Point;
  framing?: "wide" | "close";
  paused?: boolean;
  className?: string;
  onQualityChange?: (quality: Quality) => void;
}
export const clamp01 = (value: number | undefined, fallback: number): number =>
  value === undefined || !Number.isFinite(value) ? fallback : Math.max(0, Math.min(1, value));
export const displayStage = (stage: Stage): "egg" | "larva" | "pupa" | "adult" =>
  stage.startsWith("larva") || stage === "wandering" ? "larva" : stage as "egg" | "pupa" | "adult";
