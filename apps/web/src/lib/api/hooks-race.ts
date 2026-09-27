"use client";

import { useQuery } from "@tanstack/react-query";
import { api, unwrap } from "./client";
import { useApiMutation, useApiQuery } from "./query";
import type { components } from "./schema";

export type CurrentRace = components["schemas"]["CurrentRace"];
export type RaceReplay = components["schemas"]["RaceReplay"];
export type EnterRace = components["schemas"]["EnterRace"];

export const useCurrentRace = () => useQuery({
  queryKey: ["race"],
  queryFn: ({ signal }) => unwrap(api.GET("/v1/races/current", { signal })),
  refetchInterval: 10_000,
});
export const useRaceRanking = (week: string) => useApiQuery(
  ["race-ranking", week], signal => unwrap(api.GET("/v1/races/current/ranking", { signal })),
);
export const useEnterRace = () => useApiMutation(
  (body: EnterRace, headers) => unwrap(api.POST("/v1/races/current/entry", { body, headers })),
  ["race", "race-ranking"],
);
export const useRaceReplay = (id: string) => useQuery({
  queryKey: ["race-replay", id], enabled: Boolean(id),
  queryFn: ({ signal }) => unwrap(api.GET("/v1/races/entries/{entry_id}/replay", {
    signal, params: { path: { entry_id: id } },
  })),
  refetchInterval: query => ["pending", "running"].includes(query.state.data?.entry.status ?? "") ? 1000 : false,
});
