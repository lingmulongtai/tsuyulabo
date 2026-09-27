"use client";
import { api, unwrap } from "./client";
import { useApiMutation, useApiQuery } from "./query";

export const useAdults = () => useApiQuery(["adults"], signal => unwrap(api.GET("/v1/adults", { signal })));
export const useAdult = (id: string) => useApiQuery(["adults", id], signal => unwrap(api.GET("/v1/adults/{adult_id}", { signal, params: { path: { adult_id: id } } })), Boolean(id));
export const useRenameAdult = () => useApiMutation(({ id, name }: { id: string; name: string }, headers) => unwrap(api.PATCH("/v1/adults/{adult_id}", { headers, params: { path: { adult_id: id } }, body: { name } })), ["adults", "team", "friends", "me"]);
export const useLevelUp = () => useApiMutation((id: string, headers) => unwrap(api.POST("/v1/adults/{adult_id}/level-up", { headers, params: { path: { adult_id: id } } })), ["adults", "team", "me"]);
export const useTeam = () => useApiQuery(["team"], signal => unwrap(api.GET("/v1/team", { signal })));
export const useSetTeam = () => useApiMutation((adult_ids: string[], headers) => unwrap(api.PUT("/v1/team", { headers, body: { adult_ids } })), ["team", "adults"]);
export const useCollect = () => useApiMutation((_: void, headers) => unwrap(api.POST("/v1/team/collect", { headers })), ["team", "adults", "inventory", "me"]);
export const useInventory = () => useApiQuery(["inventory"], signal => unwrap(api.GET("/v1/inventory", { signal })));
export const useZukan = () => useApiQuery(["zukan"], signal => unwrap(api.GET("/v1/zukan", { signal })));
