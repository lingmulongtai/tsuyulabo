"use client";
import { useQuery } from "@tanstack/react-query";
import { api, unwrap } from "./client";
import type { components } from "./schema";
import { useApiMutation, useApiQuery } from "./query";

export const useShioriMemo = () => useApiQuery(["memo"], signal => unwrap(api.GET("/v1/shiori/memo", { signal })));
export const useShioriAsk = () => useApiMutation((question: string, headers) => unwrap(api.POST("/v1/shiori/ask", { body: { question }, headers })));
export function useJob(id?: string) {
  return useQuery({ queryKey: ["jobs", id], enabled: Boolean(id),
    queryFn: ({ signal }) => unwrap(api.GET("/v1/jobs/{job_id}", { signal, params: { path: { job_id: id! } } })),
    retry: 1,
    refetchInterval: query => query.state.error || (query.state.data && ["succeeded", "failed"].includes(query.state.data.status)) ? false : 1500,
  });
}
export const useBehavior = (fly_id: string, scenario = "rest") => useApiQuery(["behavior", fly_id, scenario], signal => unwrap(api.GET("/v1/flies/{fly_id}/behavior", { signal, params: { path: { fly_id }, query: { scenario } } })), Boolean(fly_id));
export const useExperiment = () => useApiMutation(({ fly_id, ...body }: components["schemas"]["ExperimentRequest"] & { fly_id: string }, headers) => unwrap(api.POST("/v1/flies/{fly_id}/experiments", { params: { path: { fly_id } }, body, headers })));
export const useDevTime = () => useApiQuery(["dev-time"], signal => unwrap(api.GET("/v1/dev/time", { signal })));
const timeKeys = ["dev-time", "clock", "weeks", "presentation", "team", "adults", "memo", "behavior", "zukan"];
export const useAdvanceTime = () => useApiMutation((body: components["schemas"]["AdvanceRequest"], headers) => unwrap(api.POST("/v1/dev/time/advance", { body, headers })), timeKeys);
export const useResetTime = () => useApiMutation((_: void, headers) => unwrap(api.POST("/v1/dev/time/reset", { headers })), timeKeys);
