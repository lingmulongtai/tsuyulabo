"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { buzz } from "@/game/audio/haptics";
import * as Sound from "@/game/audio/sound";
import { CUE_INFO, VALENCE_INFO } from "@/game/labels";
import { cellToRC, createTrainingGame, isSolved, starsFor, truncateTo, tryStep, type TrainingState } from "@/game/puzzles/training";
import type { Stars, TrainingParams, TrainingSubmission } from "@/game/puzzles/types";
import { Button } from "../ui/primitives";

export interface TrainingFinish {
  submission: TrainingSubmission;
  stars: Stars;
  elapsedMs: number;
}

/**
 * しつけ — the circuit puzzle. Start on the yellow 1, pass the numbers in order, fill every cell, end on the red
 * reward. Solving faster gives more stars, which become the learning strength in the mushroom body model.
 */
export function TrainingGame({ params, onFinish }: { params: TrainingParams; onFinish: (r: TrainingFinish) => void }) {
  const { n } = params;
  const [game, setGame] = useState<TrainingState>(() => createTrainingGame(params));
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(false);
  const [won, setWon] = useState<TrainingFinish | null>(null);
  const [bad, setBad] = useState<number | null>(null);
  const [lit, setLit] = useState(0);

  const boardRef = useRef<HTMLDivElement>(null);
  const startRef = useRef(0);
  const gameRef = useRef(game);
  const dragging = useRef(false);

  const cp = useMemo(() => new Map(params.checkpoints.map((c) => [c.cell, c.k])), [params]);
  const maxK = params.checkpoints[params.checkpoints.length - 1].k;
  const visitedK = game.path.filter((c) => cp.has(c)).length;

  useEffect(() => {
    gameRef.current = game;
  }, [game]);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setElapsed(performance.now() - startRef.current), 100);
    return () => clearInterval(id);
  }, [running]);

  // cascade of lit cells after a win
  useEffect(() => {
    if (!won) return;
    const id = setInterval(() => setLit((l) => (l >= n * n ? l : l + 1)), 26);
    return () => clearInterval(id);
  }, [won, n]);

  const cellAt = (x: number, y: number) => {
    const el = boardRef.current;
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const c = Math.floor(((x - r.left) / r.width) * n);
    const row = Math.floor(((y - r.top) / r.height) * n);
    if (c < 0 || row < 0 || c >= n || row >= n) return null;
    return row * n + c;
  };

  const flashBad = (cell: number) => {
    setBad(cell);
    Sound.bad();
    setTimeout(() => setBad(null), 260);
  };

  const step = (cell: number) => {
    const cur = gameRef.current;
    if (won) return;
    const next = tryStep(cur, cell);
    if (next === cur) {
      const last = cur.path[cur.path.length - 1];
      if (cell !== last && (cur.path.length === 0 || cp.has(cell))) flashBad(cell);
      return;
    }
    if (cur.path.length === 0) {
      startRef.current = performance.now();
      setRunning(true);
    }
    gameRef.current = next;
    setGame(next);
    if (next.path.length > cur.path.length) Sound.step(next.path.length - 1);
    if (isSolved(next)) {
      const ms = Math.round(performance.now() - startRef.current);
      const stars = starsFor(n, ms);
      setRunning(false);
      setElapsed(ms);
      dragging.current = false;
      Sound.puzzleClear();
      buzz([25, 30, 25]);
      setWon({ submission: { path: next.path, elapsed_ms: ms }, stars, elapsedMs: ms });
      for (let i = 0; i < stars; i++) setTimeout(() => Sound.star(i), 450 + i * 280);
    }
  };

  const onDown = (e: React.PointerEvent) => {
    e.preventDefault();
    Sound.init();
    const cell = cellAt(e.clientX, e.clientY);
    if (cell === null || won) return;
    const cur = gameRef.current;
    const pos = cur.path.indexOf(cell);
    if (pos >= 0 && pos < cur.path.length - 1) {
      const next = truncateTo(cur, cell);
      gameRef.current = next;
      setGame(next);
    } else {
      step(cell);
    }
    dragging.current = true;
    try {
      (e.target as Element).setPointerCapture(e.pointerId);
    } catch {
      // pointer capture is a nicety; dragging still works through pointermove on the board
    }
  };

  const onMove = (e: React.PointerEvent) => {
    if (!dragging.current) return;
    const cell = cellAt(e.clientX, e.clientY);
    if (cell !== null) step(cell);
  };

  const reset = () => {
    const fresh = createTrainingGame(params);
    gameRef.current = fresh;
    setGame(fresh);
    setRunning(false);
    setElapsed(0);
  };

  const points = game.path
    .map((cell) => {
      const { r, c } = cellToRC(n, cell);
      return `${c * 100 + 50},${r * 100 + 50}`;
    })
    .join(" ");

  const cue = CUE_INFO[params.cue];
  const valence = VALENCE_INFO[params.valence];

  return (
    <div className="flex select-none flex-col gap-3">
      <div className="rounded-2xl bg-tint-ai px-4 py-2 text-sm">
        教えること：<b>{cue.name}</b> ＋ <b>{valence.name}</b>
      </div>

      <div className="flex items-end justify-between px-1">
        <div className="text-xs text-muted">
          マス <span className="font-mono tabular text-ink">{game.path.length}/{n * n}</span>　数字{" "}
          <span className="font-mono tabular text-ink">{visitedK}/{maxK}</span>
        </div>
        <div className="font-mono text-2xl tabular">
          {(elapsed / 1000).toFixed(1)}
          <span className="text-sm">秒</span>
        </div>
      </div>

      <div
        ref={boardRef}
        onPointerDown={onDown}
        onPointerMove={onMove}
        onPointerUp={() => (dragging.current = false)}
        onPointerCancel={() => (dragging.current = false)}
        className="relative grid aspect-square w-full touch-none gap-[4px] rounded-3xl bg-[#1e2c29]/90 p-[6px] shadow-[var(--shadow)]"
        style={{ gridTemplateColumns: `repeat(${n}, 1fr)` }}
        role="application"
        aria-label="回路パズル"
      >
        {Array.from({ length: n * n }, (_, cell) => {
          const on = game.path.includes(cell);
          const order = game.path.indexOf(cell);
          const isLit = won && order >= 0 && order < lit;
          const k = cp.get(cell);
          return (
            <div
              key={cell}
              className={`relative grid place-items-center rounded-xl transition-colors duration-150 ${
                bad === cell ? "bg-eye/70" : isLit ? "bg-[#fff7d6]" : on ? "bg-white/18" : "bg-white/6"
              }`}
            >
              {k !== undefined && (
                <span
                  className={`z-10 grid size-[62%] place-items-center rounded-full font-mono text-lg font-bold shadow ${
                    k === 1 ? "bg-[#ffd66b] text-[#3d2a05]" : k === maxK ? "bg-[#ff6b8b] text-white" : "bg-white text-[#1e2c29]"
                  }`}
                >
                  {k}
                </span>
              )}
            </div>
          );
        })}
        <svg className="pointer-events-none absolute inset-[6px]" viewBox={`0 0 ${n * 100} ${n * 100}`} preserveAspectRatio="none" aria-hidden>
          <defs>
            <linearGradient id="zipG" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#FFD66B" />
              <stop offset=".5" stopColor="#7EE0C8" />
              <stop offset="1" stopColor="#FF6B8B" />
            </linearGradient>
          </defs>
          <polyline points={points} fill="none" stroke="url(#zipG)" strokeWidth={30} strokeLinecap="round" strokeLinejoin="round" opacity={0.92} />
        </svg>
      </div>

      <div className="flex items-center justify-between px-1 text-xs text-muted">
        <span>黄色い 1 からなぞって、数字の順に全部のマスを通ろう</span>
        <button type="button" onClick={reset} className="rounded-xl border border-line-soft bg-surface-2 px-3 py-1 font-bold text-ink">
          やり直す
        </button>
      </div>

      {won && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[#10201d]/55 p-6 backdrop-blur-[2px]">
          <div className="w-full max-w-sm rounded-[28px] bg-surface-2 p-6 text-center shadow-2xl pop-in">
            {won.stars === 3 && <div className="font-mono text-sm font-bold tracking-[0.3em] text-banana">PERFECT</div>}
            <div className="font-kiwi text-2xl">つながった！</div>
            <div className="my-2 flex justify-center gap-2 text-4xl">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className={i < won.stars ? "text-[#ffc83d] pop-in" : "text-line-soft"}
                  style={{ animationDelay: `${450 + i * 280}ms` }}
                >
                  ★
                </span>
              ))}
            </div>
            <div className="text-sm text-muted">タイム {(won.elapsedMs / 1000).toFixed(1)}秒</div>
            <Button className="mt-5" block size="lg" tone="ai" onClick={() => onFinish(won)}>
              ツユに教える
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
