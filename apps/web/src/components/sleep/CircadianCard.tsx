"use client";

import { useId, useRef } from "react";
import type { components } from "@/lib/api/schema";
import { Shiori } from "../art/Shiori";
import { Button, Card, TruthBadge } from "../ui/primitives";
import { CircadianRing } from "./CircadianRing";

export function CircadianCard({ circadian }: { circadian: components["schemas"]["CircadianResponse"] }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  return <Card className="p-4">
    <div className="flex items-center gap-4">
      <CircadianRing gauge={circadian.gauge} />
      <div className="min-w-0 flex-1">
        <h2 className="font-kiwi text-lg">体内時計ゲージ</h2>
        <p className="mt-1 text-xs text-muted">いつもの時間（日本時間）</p>
        <dl className="mt-2 space-y-1 text-sm">
          <div className="flex justify-between gap-2"><dt>おやすみ</dt><dd className="font-mono font-bold">{circadian.typical_bedtime ?? "—"}</dd></div>
          <div className="flex justify-between gap-2"><dt>おはよう</dt><dd className="font-mono font-bold">{circadian.typical_wake ?? "—"}</dd></div>
        </dl>
        <p className="mt-2 text-xs text-ai">6〜9時間のおやすみ · {circadian.streak}日連続</p>
      </div>
    </div>
    {circadian.typical_bedtime === null && circadian.typical_wake === null &&
      <p className="mt-3 text-sm text-muted">いつもの時間はまだありません。おやすみとおはようを記録して、少しずつ月を満たそう。</p>}
    <Button tone="plain" size="sm" block className="mt-3" onClick={() => dialog.current?.showModal()}>体内時計って？</Button>
    <dialog ref={dialog} aria-labelledby={titleId}
      className="fixed inset-x-0 bottom-0 top-auto m-0 mx-auto max-h-[85dvh] w-full max-w-md overflow-y-auto rounded-t-[28px] border border-line-soft bg-surface-2 p-6 pb-[max(24px,env(safe-area-inset-bottom))] text-ink shadow-2xl backdrop:bg-[#10201d]/65 backdrop:backdrop-blur-sm sm:bottom-auto sm:top-1/2 sm:-translate-y-1/2 sm:rounded-[28px]">
      <h2 id={titleId} className="font-kiwi text-xl">月のように、少しずつ</h2>
      <div className="mt-4 flex items-start gap-3 rounded-2xl bg-tint-ai p-3">
        <Shiori className="size-12 shrink-0" label="シオリ" />
        <div><p className="text-xs font-bold text-ai">シオリのひとこと</p>
          <p className="mt-1 text-sm leading-relaxed">「毎日だいたい同じ時間に、おやすみとおはよう。ツユといっしょに、暮らしのリズムを見つけていこうね。」</p></div>
      </div>
      <div className="mt-4 space-y-2 text-sm leading-relaxed">
        <TruthBadge kind="game" />
        <p>最近7回のおやすみ・おはようの時間がそろうほど、月が満ちていきます。6〜9時間のおやすみには加点も。記録が少ないあいだは、少しずつたまります。</p>
        <p>チームのげんき回復は最大1.3倍に。おはよう時にゲージが80以上なら、しずくが20増えます。</p>
        <p className="text-xs text-muted">連続日数は、6〜9時間のおやすみが続いた日数（最大7日）です。日が空いても月は減りません。このゲージはゲームの指標です。</p>
      </div>
      <div className="mt-4 space-y-2 border-t border-line-soft pt-4 text-sm leading-relaxed">
        <TruthBadge kind="real" />
        <p>ハエの時計遺伝子 period と timeless が作るタンパク質は、自分たちの遺伝子の働きを抑えることで、約24時間のリズムを生みます。脳の時計ニューロンが睡眠や活動のリズムを調整しています。この分子時計の研究は、2017年のノーベル賞につながりました。</p>
        <a className="text-xs text-leaf underline" href="https://www.nobelprize.org/prizes/medicine/2017/advanced-information/1000/" target="_blank" rel="noreferrer">ノーベル賞の公式解説（英語）</a>
      </div>
      <Button tone="ai" block className="mt-5" onClick={() => dialog.current?.close()}>わかった</Button>
    </dialog>
  </Card>;
}
