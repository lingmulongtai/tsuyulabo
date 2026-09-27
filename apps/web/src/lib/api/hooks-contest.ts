"use client";

import { api, unwrap } from "./client";
import { useApiMutation, useApiQuery } from "./query";

export type Layout = Record<"vial" | "background" | "left" | "right" | "accessory", string | null>;
export interface DecorationInventory {
  catalog: { id: string; kind: string; name: string }[];
  owned: { id: string; source: string }[];
  layout: Layout;
}
export interface ContestEntry {
  id: string; user_id: string; display_name: string; adult_name: string;
  adult_id: string; strain: string; sex: string; layout: Layout;
  entered_at: string; is_me: boolean; votes: number | null; rank?: number;
}
export interface CurrentContest {
  week: string; theme: string; phase: "entry" | "vote" | "results";
  entry_close: string; vote_close: string; votes_left: number;
  voted_entry_ids: string[];
  my_entry: ContestEntry | null; friends: ContestEntry[];
}
export interface ContestResults { week: string; entries: ContestEntry[] }

export const useDecorations = () => useApiQuery(["decorations"], async signal =>
  await unwrap(api.GET("/v1/decorations", { signal })) as unknown as DecorationInventory,
);
export const useEquipDecorations = () => useApiMutation(
  (body: Layout, headers) => unwrap(api.PUT("/v1/decorations/layout", { body, headers })),
  ["decorations"],
);
export const useCurrentContest = () => useApiQuery(["contest"], async signal =>
  await unwrap(api.GET("/v1/contest/current", { signal })) as unknown as CurrentContest,
);
export const useContestResults = () => useApiQuery(["contest-results"], async signal =>
  await unwrap(api.GET("/v1/contest/results", { signal })) as unknown as ContestResults,
);
export const useEnterContest = () => useApiMutation(
  (adult_id: string, headers) => unwrap(api.POST("/v1/contest/current/entry", { body: { adult_id }, headers })),
  ["contest", "contest-results"],
);
export const useVoteContest = () => useApiMutation(
  (entry_id: string, headers) => unwrap(api.POST("/v1/contest/current/votes", { body: { entry_id }, headers })),
  ["contest", "contest-results"],
);
