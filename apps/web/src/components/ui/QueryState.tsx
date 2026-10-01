"use client";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { Button, Card } from "./primitives";

export function LoadingCard() {
  return <Card className="space-y-4 p-6"><p role="status" className="text-sm text-muted">研究ノートを開いています…</p>
    <div className="h-48 rounded-3xl bg-tint-leaf motion-safe:animate-pulse" />
    <div className="h-6 w-2/3 rounded-full bg-line-soft motion-safe:animate-pulse" />
    <div className="h-12 rounded-2xl bg-line-soft motion-safe:animate-pulse" /></Card>;
}

export function ErrorCard({ error, retry }: { error: unknown; retry?: () => void }) {
  return <Card className="space-y-3 p-5"><div role="alert">
    <h2 className="font-kiwi text-lg">{error instanceof ApiError && !error.retryable ? "研究ノートからのお知らせ" : "研究所とつながるのを待っています"}</h2>
    <p className="mt-2 text-sm text-muted">{error instanceof Error ? error.message : "通信を確認して、もう一度お試しください。"}</p>
  </div>{retry && (error instanceof ApiError && error.retryAfter > 0
    ? <CooldownRetry key={error.retryAt} error={error} retry={retry} />
    : <Button tone="leaf" onClick={retry}>もう一度ためす</Button>)}</Card>;
}

function CooldownRetry({ error, retry }: { error: ApiError; retry: () => void }) {
  const [remaining, setRemaining] = useState(() => Math.max(0, Math.ceil((error.retryAt - Date.now()) / 1000)));
  useEffect(() => {
    const timer = setInterval(() => setRemaining(Math.max(0, Math.ceil((error.retryAt - Date.now()) / 1000))), 1000);
    return () => clearInterval(timer);
  }, [error]);
  return <Button tone="leaf" disabled={remaining > 0} onClick={retry}>{remaining > 0 ? `${remaining}秒待ってね` : "もう一度ためす"}</Button>;
}

export function QueryState<T>({ query, children }: {
  query: { data: T | undefined; isPending: boolean; error: Error | null; refetch: () => unknown };
  children: (data: T) => ReactNode;
}) {
  if (query.data !== undefined) return <>{query.error && <ErrorCard error={query.error} retry={() => void query.refetch()} />}{children(query.data)}</>;
  if (query.error) return <ErrorCard error={query.error} retry={() => void query.refetch()} />;
  return <LoadingCard />;
}
