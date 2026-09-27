"use client";

import { api, unwrap } from "./client";
import type { components } from "./schema";
import { useApiMutation, useApiQuery } from "./query";

const changes = ["mating", "pending-eggs", "adults", "notifications"];

export const useMatingInbox = () => useApiQuery(["mating", "inbox"], signal => unwrap(api.GET("/v1/weeks/friend-mating", { signal })));
export const useMatingOptions = (friend_id: string) => useApiQuery(["mating", "options", friend_id], signal => unwrap(api.GET("/v1/weeks/friend-mating/options/{friend_id}", { signal, params: { path: { friend_id } } })));
export const useProposeMating = () => useApiMutation((body: components["schemas"]["ProposeMating"], headers) => unwrap(api.POST("/v1/weeks/friend-mating", { body, headers })), changes);
export const useAcceptMating = () => useApiMutation((proposal_id: string, headers) => unwrap(api.POST("/v1/weeks/friend-mating/{proposal_id}/accept", { headers, params: { path: { proposal_id } } })), changes);
export const useDeclineMating = () => useApiMutation((proposal_id: string, headers) => unwrap(api.POST("/v1/weeks/friend-mating/{proposal_id}/decline", { headers, params: { path: { proposal_id } } })), changes);
export const usePendingEggs = () => useApiQuery(["pending-eggs"], signal => unwrap(api.GET("/v1/weeks/pending-eggs", { signal })));
