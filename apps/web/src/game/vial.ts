import type { Behaviour, Habitat, Point } from "@/components/vivarium/types";
import type { components } from "@/lib/api/schema";

export type VialState = components["schemas"]["Vial"];
const actions: Behaviour[] = ["rest", "walk", "turn_left", "turn_right", "feed", "escape", "groom", "approach", "avoid"];
/** Select the finite decoder maximum; never invent a brain decision. */
export function decodedBehaviour(value: unknown): Behaviour {
  if (!value || typeof value !== "object") return "rest";
  const scores = Object.entries(value).filter(([action, p]) => actions.includes(action as Behaviour) && typeof p === "number" && Number.isFinite(p));
  scores.sort((a, b) => Number(b[1]) - Number(a[1]));
  return (scores[0]?.[0] as Behaviour | undefined) ?? "rest";
}
export function odourBehaviour(value: unknown): Behaviour | undefined {
  if (!value || typeof value !== "object") return;
  const { toward, away } = value as Record<string, unknown>;
  if (typeof toward !== "number" || typeof away !== "number" || !Number.isFinite(toward + away) || toward < 0 || away < 0 || toward + away === 0) return;
  return toward > away ? "approach" : away > toward ? "avoid" : "rest";
}
export function habitat(vial?: VialState | null): Habitat {
  return vial ? { food: vial.food, humidity: vial.humidity, mould: vial.mould, grime: vial.grime, pupaAge: vial.pupa_age, temperature: vial.temperature, pace: vial.pace } : {};
}
export function sitePosition(value?: readonly number[]): Point {
  return value?.length === 3 && value.every(Number.isFinite) ? [value[0], value[1], value[2]] : [0.24, -0.05, 0.94];
}
