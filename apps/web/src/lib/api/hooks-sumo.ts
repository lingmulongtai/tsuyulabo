"use client";

import { useApiMutation, useApiQuery } from "./query";
import { api, unwrap } from "./client";
import type { components } from "./schema";

export type BoutReplay = components["schemas"]["BoutReplay"];
export type StartBout = components["schemas"]["StartBout"];

export const useSumoChallenges = () => useApiQuery(
  ["sumo-challenges"], signal => unwrap(api.GET("/v1/sumo/challenges", { signal })),
);
export const useSumoHistory = () => useApiQuery(
  ["sumo-history"], signal => unwrap(api.GET("/v1/sumo/bouts", { signal })),
);
export const useStartSumo = () => useApiMutation(
  (body: StartBout, headers) => unwrap(api.POST("/v1/sumo/bouts", { body, headers })),
  ["sumo-challenges", "sumo-history", "home"],
);
export const useSumoReplay = (id: string) => useApiQuery(
  ["sumo-replay", id], signal => unwrap(api.GET("/v1/sumo/bouts/{bout_id}", {
    signal, params: { path: { bout_id: id } },
  })), Boolean(id),
);
