"use client";
import Link from "next/link";
import { HomeScreen } from "@/components/home/HomeScreen";
import { AppShell } from "@/components/shell/AppShell";
import { BreedingStart } from "@/components/breeding/BreedingStart";
import { QueryState } from "@/components/ui/QueryState";
import { useHome } from "@/lib/api/hooks";

export default function Home() {
  const home = useHome();
  return (
    <AppShell>
      <div className="py-3"><QueryState query={home}>{data => <HomeScreen data={data} hero={!data.week && <BreedingStart />} footer={<>
        <Link href="/shiori" className="rounded-2xl bg-tint-ai p-3 text-center font-bold text-ai">シオリに聞く</Link>
        <Link href="/care/meal?practice=1" className="text-center text-sm text-muted underline">ごはんづくりの練習</Link>
      </>} />}</QueryState></div>
    </AppShell>
  );
}
