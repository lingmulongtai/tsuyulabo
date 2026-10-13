"use client";
import { useState } from "react";
import { CareVial } from "../vivarium/CareVial";
import type { Point } from "../vivarium/types";
import type { PupationSiteParams, PupationSiteSubmission } from "@/game/puzzles/types";
import { Button } from "../ui/primitives";
import { ShioriBubble } from "../home/ShioriBubble";

const position = (option: PupationSiteParams["options"][number], i: number): Point =>
  option.position ? [option.position[0], option.position[1], option.position[2]] : [0.24, [0.55, -1, 1.15][i], 0.94];

export function PupationSiteGame({ params, onFinish }: { params: PupationSiteParams; onFinish: (value: PupationSiteSubmission) => void }) {
  const [choice, setChoice] = useState<string | null>(null);
  const target = params.options.findIndex(option => option.id === choice);
  const selected = target < 0 ? undefined : position(params.options[target], target);
  return <div className="space-y-3">
    <p className="text-sm text-muted">幼虫が壁を登っています。ガラスを触れて、止まる場所を選びましょう。</p>
    <CareVial stage={choice ? "pupa" : "wandering"} behaviour="walk" pupationPosition={selected}
      onGlassPick={point => {
        const closest = [...params.options].sort((a, b) => Math.abs(position(a, params.options.indexOf(a))[1] - point[1]) - Math.abs(position(b, params.options.indexOf(b))[1] - point[1]))[0];
        setChoice(closest.id);
      }} />
    <ShioriBubble title="シオリのヒント" text={params.hint} />
    <p className="text-xs text-muted">ヒントが外れることもあります。</p>
    <div className="grid gap-2">{params.options.map(option => <button key={option.id} aria-pressed={choice === option.id} onClick={() => setChoice(option.id)} className="glass-panel min-h-11 rounded-lg border border-line p-3 text-left">
      <span className="block text-sm">{option.label}</span><span className="text-xs text-muted">{option.detail}</span>
    </button>)}</div>
    <Button block disabled={!choice} onClick={() => { if (choice) onFinish({ choice }); }}>この場所で見守る</Button>
  </div>;
}
