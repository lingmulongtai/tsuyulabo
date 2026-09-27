"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { TemperatureGame } from "@/components/games/TemperatureGame";
import { PuzzleSession } from "@/components/games/PuzzleSession";
export default function TemperaturePage() {
  return <AppShell hideTabs><CareFrame title="温度あわせ" subtitle="ゆれる針を、ぴったり25℃に">
    <PuzzleSession kind="temperature">{(params, finish) => <TemperatureGame params={params} onFinish={finish} />}</PuzzleSession>
  </CareFrame></AppShell>;
}
