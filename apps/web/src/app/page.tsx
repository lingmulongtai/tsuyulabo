"use client";
import Link from "next/link";
import { HomeScreen } from "@/components/home/HomeScreen";
import { AppShell } from "@/components/shell/AppShell";
import { FlyArt } from "@/components/art/FlyArt";
import { Button, Card } from "@/components/ui/primitives";
import { ErrorCard, QueryState } from "@/components/ui/QueryState";
import { useHome, useStartWeek } from "@/lib/api/hooks";

export default function Home() {
  const home = useHome();
  const start = useStartWeek();
  return (
    <AppShell>
      <div className="py-3"><QueryState query={home}>{data => <HomeScreen data={data} hero={!data.week && <Card className="p-5 text-center">
          <FlyArt stage="egg" className="mx-auto h-40 w-40" />
          <h2 className="font-kiwi text-xl">新しい一週間をはじめよう</h2>
          <p className="mb-4 text-sm text-muted">小さな卵から、どんなツユに育つかな。</p>
          <Button block size="lg" disabled={start.isPending} onClick={() => start.mutate()}>{start.isPending ? "卵を受け取り中…" : "卵を受け取る"}</Button>
          {start.error && <ErrorCard error={start.error} retry={() => start.mutate()} />}
        </Card>} footer={<>
        <Link href="/shiori" className="rounded-2xl bg-tint-ai p-3 text-center font-bold text-ai">シオリに聞く</Link>
        <Link href="/care/meal?practice=1" className="text-center text-sm text-muted underline">ごはんづくりの練習</Link>
      </>} />}</QueryState></div>
    </AppShell>
  );
}
