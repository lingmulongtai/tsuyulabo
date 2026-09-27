"use client";
import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, createAction } from "./client";

export function useApiQuery<T>(key: readonly unknown[], read: (signal: AbortSignal) => Promise<T>, enabled = true) {
  return useQuery({ queryKey: key, queryFn: ({ signal }) => read(signal), enabled,
    retry: (count, error) => count < 1 && error instanceof ApiError && error.retryable });
}

/** An unresolved action keeps its key, including when the player presses retry. */
export function useApiMutation<T, V = void>(write: (variables: V, headers: Record<string, string>) => Promise<T>, invalidate: string[] = []) {
  const cache = useQueryClient();
  const pending = useRef<{ signature: string; action: ReturnType<typeof createAction<T>> } | null>(null);
  return useMutation({ retry: false,
    mutationFn: async (variables: V) => {
      const signature = JSON.stringify(variables) ?? "void";
      if (!pending.current || pending.current.signature !== signature) {
        pending.current = { signature, action: createAction(headers => write(variables, headers)) };
      }
      const current = pending.current;
      try {
        const result = await current.action.run();
        if (pending.current === current) pending.current = null;
        return result;
      } catch (error) {
        if (error instanceof ApiError && !error.retryable && pending.current === current) pending.current = null;
        throw error;
      }
    },
    onSettled: async () => {
      await Promise.all([...new Set(["home", ...invalidate])].map(key => cache.invalidateQueries({ queryKey: [key] })));
    },
  });
}
