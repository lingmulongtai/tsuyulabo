"use client";
import { api, unwrap } from "./client";
import type { components } from "./schema";
import { useApiMutation, useApiQuery } from "./query";

export const useFriends = () => useApiQuery(["friends"], signal => unwrap(api.GET("/v1/friends", { signal })));
export const useAddFriend = () => useApiMutation((friend_code: string, headers) => unwrap(api.POST("/v1/friends", { body: { friend_code }, headers })), ["friends"]);
export const useRemoveFriend = () => useApiMutation((friend_id: string, headers) => unwrap(api.DELETE("/v1/friends/{friend_id}", { params: { path: { friend_id } }, headers })), ["friends"]);
export const useFriendLab = (friend_id: string) => useApiQuery(["friends", friend_id, "lab"], signal => unwrap(api.GET("/v1/friends/{friend_id}/lab", { signal, params: { path: { friend_id } } })), Boolean(friend_id));
export const useLike = () => useApiMutation((friend_id: string, headers) => unwrap(api.POST("/v1/friends/{friend_id}/like", { params: { path: { friend_id } }, headers })), ["friends", "notifications"]);
export const useGift = () => useApiMutation(({ friend_id, ...body }: components["schemas"]["SendGift"] & { friend_id: string }, headers) => unwrap(api.POST("/v1/friends/{friend_id}/gift", { params: { path: { friend_id } }, body, headers })), ["inventory", "friends", "me"]);
export const useNotifications = () => useApiQuery(["notifications"], signal => unwrap(api.GET("/v1/notifications", { signal })));
