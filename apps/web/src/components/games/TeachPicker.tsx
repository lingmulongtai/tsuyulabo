"use client";

import { useState } from "react";
import { CUE_INFO, VALENCE_INFO } from "@/game/labels";
import type { Cue, Valence } from "@/game/puzzles/types";
import { ShioriBubble } from "../home/ShioriBubble";
import { Button, TruthBadge } from "../ui/primitives";

const CUES: Cue[] = ["banana", "apple_vinegar", "yeast", "grape", "blue_light"];
const CUE_COLOR: Record<Cue, string> = {
  banana: "#F2C94C",
  apple_vinegar: "#E5484D",
  yeast: "#E6D5B4",
  grape: "#8E6BD8",
  blue_light: "#5EC8F2",
};

/** Choose what to teach before the circuit puzzle: a cue (odour / light) and a sweet or bitter outcome. */
export function TeachPicker({ remaining, tip, disabled, onPick }: { remaining?: number; tip?: string; disabled?: boolean; onPick: (cue: Cue, valence: Valence) => void }) {
  const [cue, setCue] = useState<Cue>("banana");
  const [valence, setValence] = useState<Valence>("reward");

  return (
    <div className="flex flex-col gap-4">
      <ShioriBubble
        title="しつけのコーチ"
        text={tip ?? "匂いや光の合図と、あまい・にがいごはんを組み合わせて覚えさせます。パズルが速くきれいに解けるほど、しっかり覚えます。"}
      />

      <section>
        <div className="mb-2 flex items-center gap-2 px-1 text-sm font-bold">
          合図をえらぶ <TruthBadge kind="real" />
        </div>
        <div className="grid grid-cols-5 gap-2">
          {CUES.map((c) => (
            <button
              type="button"
              key={c}
              onClick={() => setCue(c)}
              aria-pressed={cue === c}
              className={`press flex flex-col items-center gap-1 whitespace-nowrap rounded-2xl border-2 bg-surface-2 py-2 text-[0.66rem] font-bold ${cue === c ? "border-ai" : "border-line-soft"}`}
            >
              <span className="size-7 rounded-full shadow-inner" style={{ background: c === "blue_light" ? "radial-gradient(circle,#dff6ff,#5ec8f2)" : CUE_COLOR[c] }} />
              {CUE_INFO[c].short}
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-2 px-1 text-sm font-bold">いっしょに出すもの</div>
        <div className="grid grid-cols-2 gap-2">
          {(["reward", "punish"] as const).map((v) => (
            <button
              type="button"
              key={v}
              onClick={() => setValence(v)}
              aria-pressed={valence === v}
              className={`press rounded-2xl border-2 bg-surface-2 px-3 py-3 text-left ${valence === v ? (v === "reward" ? "border-leaf" : "border-eye") : "border-line-soft"}`}
            >
              <div className="font-bold">{VALENCE_INFO[v].name}</div>
              <div className="text-xs text-muted">
                {CUE_INFO[cue].short}
                {VALENCE_INFO[v].effect}
              </div>
            </button>
          ))}
        </div>
      </section>

      <div className="rounded-2xl bg-bg px-4 py-2 text-xs leading-relaxed text-muted">
        本物のハエも、匂いとごほうび（または罰）を結びつけて覚えます。覚えるのは脳の「キノコ体」で、ドーパミンがつながりの強さを変えます。
      </div>

      <Button tone="ai" size="lg" block disabled={disabled || remaining === 0} onClick={() => onPick(cue, valence)}>
        パズルをはじめる{remaining !== undefined && <span className="text-sm opacity-80">（今日あと{remaining}回）</span>}
      </Button>
    </div>
  );
}
