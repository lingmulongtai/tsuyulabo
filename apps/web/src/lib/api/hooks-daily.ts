"use client";

import { useEffect } from "react";
import { api, unwrap } from "./client";
import { useApiMutation, useApiQuery } from "./query";
import type { components } from "./schema";

export type DailyCircuit = components["schemas"]["DailyCircuitResponse"];
export type DailyResult = components["schemas"]["DailyResult"];
export type DailyRanking = components["schemas"]["DailyRanking"];
export type DailySubmission = components["schemas"]["DailySubmitRequest"];

export function useDailyCircuit() {
  const query = useApiQuery(["daily-circuit"], signal => unwrap(api.GET("/v1/daily-circuit", { signal })));
  const { data, refetch } = query;
  useEffect(() => {
    if (!data) return;
    // Use the server's remaining day length, so a wrong device clock cannot change the puzzle.
    const remaining = Date.parse(data.resets_at) - Date.parse(data.server_now);
    const id = setTimeout(() => void refetch(), Math.max(100, remaining + 50));
    return () => clearTimeout(id);
  }, [data, refetch]);
  return query;
}

export const useDailyRanking = (day: string) => useApiQuery(
  ["daily-ranking", day], signal => unwrap(api.GET("/v1/daily-circuit/ranking", { signal })), Boolean(day),
);
export const useStartDaily = () => useApiMutation(
  (day: string, headers) => unwrap(api.POST("/v1/daily-circuit/start", { body: { day }, headers })),
  ["daily-circuit"],
);
export const useSubmitDaily = () => useApiMutation(
  (body: DailySubmission, headers) => unwrap(api.POST("/v1/daily-circuit/submit", { body, headers })),
  ["daily-circuit", "daily-ranking", "me"],
);
