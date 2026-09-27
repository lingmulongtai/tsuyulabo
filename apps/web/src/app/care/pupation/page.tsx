"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { PuzzleSession } from "@/components/games/PuzzleSession";
import { ShioriBubble } from "@/components/home/ShioriBubble";
import { FlyArt } from "@/components/art/FlyArt";
import * as Sound from "@/game/audio/sound";
import { buzz } from "@/game/audio/haptics";

export default function PupationPage() {
  return <AppShell hideTabs><CareFrame title="さなぎの場所えらび" subtitle="落ちついて休める場所を探そう">
    <PuzzleSession kind="pupation_site">{(params, finish) => <>
      <FlyArt stage="wandering" className="mx-auto h-36 w-48" />
      <ShioriBubble title="シオリのヒント" text={params.hint} />
      <p className="text-center text-xs text-muted">ヒントが外れることもあります。ひとつ選んでみよう。</p>
      {params.options.map((option, i) => <button key={option.id} onClick={() => { Sound.init(); Sound.tap(); buzz(15); finish({ choice: option.id }); }}
        className="press flex items-center gap-4 rounded-3xl border-2 border-leaf bg-surface-2 p-5 text-left shadow-[0_4px_0_var(--line)]">
        <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-tint-leaf font-mono text-xl text-leaf">{i + 1}</span>
        <span><span className="block font-bold">{option.label}</span><span className="text-sm text-muted">{option.detail}</span></span>
      </button>)}
    </>}</PuzzleSession>
  </CareFrame></AppShell>;
}
