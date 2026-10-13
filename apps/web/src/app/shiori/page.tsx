"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { Suspense } from "react";
import { DiaryScreen } from "@/components/shiori/DiaryScreen";

export default function ShioriPage() {
  return <AppShell><CareFrame title="観察日記" subtitle="この子と過ごした日を、読み返す">
    <Suspense fallback={<p role="status">日記を開いています…</p>}><DiaryScreen /></Suspense>
  </CareFrame></AppShell>;
}
