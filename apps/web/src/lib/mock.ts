import type { HomeData, TeamMemberSummary } from "./types";

const demoMember = (id: string, name: string, bag: number): TeamMemberSummary => ({
  id, name, strain: "wild", sex: "f", level: 12, energy: 80, bag: { banana: bag },
  week_id: "w-demo", stars: 3, traits: [], subskills: [], skills: {}, preferences: {},
  level_cap: 40, exp: 0, created_at: "2026-09-27T04:00:00+09:00", slot: 0,
  shizuku: 0, pending_exp: bag,
});

/** Sample home payload (research day 3, noon) used until the page is wired to the API, and in stories/tests. */
export const MOCK_HOME: HomeData = {
  clock: { game_now: "2026-09-30T12:40:00+09:00", slot: "noon", research_day: 3, weekday_label: "水" },
  week: { id: "w-demo", research_day: 3, stage: "larva2", ready_to_eclose: false, care_miss: 0, points_so_far: 5420 },
  fly: { stage: "larva2", hunger: 70, cleanliness: 45, mood: 60, mood_label: "ふつう", growth: 88.5 },
  todo: [
    { action: "meal", status: "done", slot: "morning" },
    { action: "meal", status: "available", slot: "noon" },
    { action: "training", status: "available", remaining: 2 },
    { action: "cleaning", status: "available" },
    { action: "meal", status: "locked", slot: "night", available_at: "2026-09-30T18:00:00+09:00" },
    { action: "sleep", status: "locked", available_at: "2026-09-30T18:00:00+09:00" },
  ],
  balances: { shizuku: 1240, research_points: 60, kohaku: 0 },
  team: {
    members: [
      demoMember("a1", "ぴかり", 9),
      { ...demoMember("a2", "こむぎ", 3), slot: 1 },
    ],
    bag_total: 12,
    collectable: true,
  },
  shiori: {
    memo: {
      text: "昨夜の睡眠は約4時間でした。朝のごはんで大成功が1回。バナナの匂いへの反応が少し強くなっています。",
      evidence: ["0412", "0413", "c-19"],
    },
  },
};
