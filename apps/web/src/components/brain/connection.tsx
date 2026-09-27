"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Button, Card } from "@/components/ui/primitives";

// Temporary connection boundary until the shared account UI lands on this branch.
export const TOKEN_KEY = "tsuyulabo.token";
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export async function readApi<T>(path: string, token: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` }, signal, cache: "no-store",
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("接続の有効期限が切れています。接続し直してください。");
    if (response.status === 404) throw new Error("この子が見つかりません。自分の飼育室の子を選んでください。");
    throw new Error("データを読み込めませんでした。少し待ってからもう一度お試しください。");
  }
  return response.json() as Promise<T>;
}

export function BrainConnection({ children }: { children: (token: string) => ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [input, setInput] = useState("");
  useEffect(() => {
    // Defer browser storage access until after hydration.
    const timer = window.setTimeout(() => {
      try { setToken(localStorage.getItem(TOKEN_KEY) ?? ""); } catch { setToken(""); }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);
  if (token === null) return <p role="status" className="text-sm text-muted">接続を確認しています…</p>;
  if (token) return <>
    {children(token)}
    <button type="button" className="mt-4 text-xs text-muted underline" onClick={() => {
      try { localStorage.removeItem(TOKEN_KEY); } catch { /* In-memory connection still works. */ }
      setToken("");
    }}>接続し直す</button>
  </>;
  return <Card className="space-y-3 p-4">
    <h2 className="font-kiwi">飼育室に接続</h2>
    <p className="text-sm text-muted">この先行版では、育てているゲストの接続トークンを使います。</p>
    <form className="space-y-3" onSubmit={(event) => {
      event.preventDefault();
      const value = input.trim();
      if (!value) return;
      try { localStorage.setItem(TOKEN_KEY, value); } catch { /* Keep this session usable without storage. */ }
      setToken(value); setInput("");
    }}>
      <label className="block text-xs" htmlFor="brain-token">接続トークン</label>
      <input id="brain-token" type="password" autoComplete="off" required value={input} onChange={(event) => setInput(event.target.value)} className="w-full rounded-xl border border-line bg-surface p-2" />
      <Button type="submit" size="sm" disabled={!input.trim()}>接続する</Button>
    </form>
  </Card>;
}
