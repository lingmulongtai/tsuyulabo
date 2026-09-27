"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FlyArt } from "@/components/art/FlyArt";
import type { Sex, Strain } from "@/components/art/palette";
import { AppShell } from "@/components/shell/AppShell";
import { Button, Card, Stars } from "@/components/ui/primitives";
import { BrainConnection, readApi } from "./connection";

interface Adult { id: string; name: string; stars: number; level: number; energy: number; sex: Sex; strain: Strain }

function Details({ id, token }: { id: string; token: string }) {
  const [adult, setAdult] = useState<Adult | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    readApi<Adult>(`/v1/adults/${encodeURIComponent(id)}`, token, controller.signal)
      .then((data) => { if (!controller.signal.aborted) setAdult(data); })
      .catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "読み込めませんでした。"); });
    return () => controller.abort();
  }, [id, token, attempt]);
  if (error) return <Card className="space-y-3 p-4"><p role="alert">{error}</p><Button size="sm" onClick={() => { setError(""); setAttempt(attempt + 1); }}>もう一度読み込む</Button></Card>;
  if (!adult) return <p role="status">この子の記録を読み込んでいます…</p>;
  return <Card className="space-y-3 p-5 text-center">
    <h1 className="font-kiwi text-2xl">{adult.name}</h1>
    <div className="mx-auto w-40"><FlyArt stage="adult" sex={adult.sex} strain={adult.strain} /></div>
    <Stars value={adult.stars} />
    <p className="text-sm">レベル {adult.level} · げんき {adult.energy}%</p>
    <Link href={`/adults/${encodeURIComponent(id)}/brain`} className="block rounded-2xl border border-leaf bg-tint-leaf p-4 font-bold text-leaf">脳をのぞく →</Link>
  </Card>;
}

export function AdultDetail({ id }: { id: string }) {
  return <AppShell hideTabs><div className="space-y-4 px-4 py-5">
    <Link href="/" className="text-sm text-leaf">← 飼育室へ</Link>
    <BrainConnection>{(token) => <Details key={`${id}:${token}`} id={id} token={token} />}</BrainConnection>
  </div></AppShell>;
}
