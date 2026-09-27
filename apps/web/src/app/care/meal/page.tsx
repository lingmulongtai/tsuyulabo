"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { CareFrame } from "@/components/games/CareFrame";
import { MealGame } from "@/components/games/MealGame";
import { PuzzleSession } from "@/components/games/PuzzleSession";
import { AppShell } from "@/components/shell/AppShell";
import { LoadingCard } from "@/components/ui/QueryState";
import { practiceMeal } from "@/game/practice";

const practiceParams = practiceMeal(2026);
function MealSession() {
  const search = useSearchParams();
  return <PuzzleSession key={search.get("practice") ?? "live"} kind="meal" practice={search.get("practice") === "1"} practiceParams={practiceParams}>
    {(params, finish) => <MealGame params={params} onFinish={result => finish(result.submission, result.score)} />}
  </PuzzleSession>;
}
export default function MealPage() {
  return <AppShell hideTabs><CareFrame title="ごはんづくり" subtitle="30秒で、材料ブロックの列をそろえて消そう">
    <Suspense fallback={<LoadingCard />}><MealSession /></Suspense>
  </CareFrame></AppShell>;
}
