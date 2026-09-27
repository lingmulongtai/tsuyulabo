"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { AskShiori } from "@/components/shiori/AskShiori";
import { ShioriBubble } from "@/components/home/ShioriBubble";
import { QueryState } from "@/components/ui/QueryState";
import { useShioriMemo } from "@/lib/api/hooks";

export default function ShioriPage() {
  const memo = useShioriMemo();
  return <AppShell><CareFrame title="シオリの研究ノート" subtitle="小さな「なんで？」を、いっしょに">
    <QueryState query={memo}>{data => data ? <ShioriBubble text={data.text} evidence={data.evidence} /> : <p className="text-sm text-muted">今朝のメモはまだありません。気になることを聞いてみよう。</p>}</QueryState>
    <AskShiori />
  </CareFrame></AppShell>;
}
