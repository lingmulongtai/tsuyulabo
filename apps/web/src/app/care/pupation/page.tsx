"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { PuzzleSession } from "@/components/games/PuzzleSession";
import { PupationSiteGame } from "@/components/games/PupationSiteGame";

export default function PupationPage() {
  return <AppShell hideTabs><CareFrame title="さなぎの場所えらび" subtitle="幼虫が落ち着ける場所を選び、羽化を見守る">
    <PuzzleSession kind="pupation_site">{(params, finish) => <PupationSiteGame params={params} onFinish={finish} />}</PuzzleSession>
  </CareFrame></AppShell>;
}
