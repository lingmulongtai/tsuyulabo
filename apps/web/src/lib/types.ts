/**
 * Client-side view of the game API (docs/specs/api.md). These mirror the server responses; once the
 * OpenAPI client is generated they become thin aliases over the generated types.
 */

import type { Stage } from "@/components/art/FlyArt";
import type { Sex, Strain } from "@/components/art/palette";

export type Slot = "morning" | "noon" | "night";
export type ActionKind = "meal" | "training" | "cleaning" | "temperature" | "pupation_site" | "sleep" | "wake";
export type TodoStatus = "done" | "available" | "locked";
export type WeekRank = "normal" | "silver" | "gold" | "rainbow";

export interface TodoItem {
  action: ActionKind;
  status: TodoStatus;
  slot?: Slot;
  remaining?: number;
  available_at?: string | null;
}

export interface TeamMemberSummary {
  id: string;
  name: string;
  strain: Strain;
  sex: Sex;
  level: number;
  energy: number;
  bag: number;
  bag_cap: number;
}

export interface HomeData {
  clock: { game_now: string; slot: Slot; research_day: number; weekday_label: string };
  week: {
    id: string;
    research_day: number;
    stage: Stage;
    ready_to_eclose: boolean;
    care_miss: number;
    points_so_far: number;
  } | null;
  fly: { stage: Stage; hunger: number; cleanliness: number; mood: number; mood_label: string; growth: number } | null;
  todo: TodoItem[];
  balances: { shizuku: number; research_points: number; kohaku: number };
  team: { members: TeamMemberSummary[]; bag_total: number; collectable: boolean };
  shiori: { memo: { text: string; evidence: string[] } | null };
}
