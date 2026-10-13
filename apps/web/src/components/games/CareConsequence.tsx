"use client";
import type { components } from "@/lib/api/schema";
import { CareVial } from "../vivarium/CareVial";
import type { PuzzleKind } from "@/game/puzzles/types";

export function CareConsequence({ kind, result }: { kind: PuzzleKind; result: components["schemas"]["PuzzleResult"] }) {
  return <section className="space-y-2" aria-label="びんに届いたお世話">
    <CareVial vial={result.vial} pour={kind === "meal"} {...(kind === "meal" ? { behaviour: "feed" as const } : kind === "pupation_site" ? { stage: "pupa" as const } : {})} />
    <p role="status" className="text-sm">{kind === "meal" ? "配合したごはんが、びんの底へ。幼虫は餌に潜って食べます。" : kind === "cleaning" ? "拭いたガラスの向こうに、この子が見えます。" : kind === "temperature" ? "温度と湿度を整えました。びんの中の様子を見てみよう。" : "選んだ場所で、さなぎを見守ります。"}</p>
  </section>;
}
