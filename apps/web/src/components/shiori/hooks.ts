"use client";
import { api, unwrap } from "@/lib/api/client";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import type { components } from "@/lib/api/schema";
import { useQuery } from "@tanstack/react-query";

export type DiaryEntry = components["schemas"]["DiaryResponse"];
export const useIndividuals = () => useApiQuery(["diary-individuals"], signal => unwrap(api.GET("/v1/shiori/individuals", { signal })));
export const useDiaryAsk = () => useApiMutation((body: components["schemas"]["AskRequest"], headers) => unwrap(api.POST("/v1/shiori/ask", { body, headers })));
export const useDiary = (fly_id: string) => useApiQuery(["diary", fly_id], signal => unwrap(api.GET("/v1/shiori/diary", { signal, params: { query: { fly_id } } })), Boolean(fly_id));
export const useHint = (fly_id: string) => useQuery({ queryKey: ["quiet-hint", fly_id], enabled: Boolean(fly_id), queryFn: ({ signal }) => unwrap(api.GET("/v1/shiori/flies/{fly_id}/hint", { signal, params: { path: { fly_id } } })), refetchInterval: query => query.state.error ? false : 60_000, retry: false });
export const useDismissHint = () => useApiMutation((hint_id: string, headers) => unwrap(api.POST("/v1/shiori/hints/{hint_id}/dismiss", { headers, params: { path: { hint_id } } })), ["quiet-hint"]);
export const useWhy = () => useApiMutation(({ fly_id, ...body }: components["schemas"]["WhyRequest"] & { fly_id: string }, headers) => unwrap(api.POST("/v1/shiori/flies/{fly_id}/why", { headers, params: { path: { fly_id } }, body })));
