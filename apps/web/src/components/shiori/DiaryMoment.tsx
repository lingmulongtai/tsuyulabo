"use client";
import { Vivarium } from "../vivarium/Vivarium";
import type { Behaviour, Habitat, Phenotype, Stage } from "../vivarium/types";
import type { DiaryEntry } from "./hooks";

const stages: Stage[] = ["egg", "larva", "larva1", "larva2", "larva3", "wandering", "pupa", "adult"];
const actions: Behaviour[] = ["rest", "walk", "turn_left", "turn_right", "feed", "escape", "groom", "approach", "avoid", "fly", "stop", "flee", "burrow"];
export function momentProps(moment: DiaryEntry["snapshot"]) {
  const stage = stages.includes(moment.stage as Stage) ? moment.stage as Stage : "egg";
  const behaviour = actions.includes(moment.behaviour as Behaviour) ? moment.behaviour as Behaviour : "rest";
  const allowed: Phenotype[] = ["wild", "white", "yellow", "ebony", "curly", "vestigial"];
  const traits = moment.phenotypes.filter((value): value is Phenotype => allowed.includes(value as Phenotype));
  return { stage, behaviour, seed: moment.seed ?? moment.record_id, environment: moment.environment as Habitat, sex: moment.sex ?? undefined, traits };
}
export function DiaryMoment({ moment }: { moment: DiaryEntry["snapshot"] }) {
  return <figure>
    <div className="h-64 overflow-hidden rounded-lg" aria-label="記録した瞬間の3D再現"><Vivarium {...momentProps(moment)} paused framing="close" quality="low" /></div>
    <figcaption className="mt-1 text-xs text-muted">記録した動きの3D再現 ・ {new Date(moment.at).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })}</figcaption>
  </figure>;
}
