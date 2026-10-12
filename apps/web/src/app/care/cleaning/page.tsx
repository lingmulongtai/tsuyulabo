"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { CleaningGame } from "@/components/games/CleaningGame";
import { PuzzleSession } from "@/components/games/PuzzleSession";
export default function CleaningPage() {
  return <AppShell hideTabs><CareFrame title="びんのおそうじ" subtitle="びんを清潔に保って、この子の健康を守る">
    <PuzzleSession kind="cleaning">{(params, finish) => <CleaningGame params={params} onFinish={finish} />}</PuzzleSession>
  </CareFrame></AppShell>;
}
