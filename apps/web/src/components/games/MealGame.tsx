"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { buzz } from "@/game/audio/haptics";
import * as Sound from "@/game/audio/sound";
import { INGREDIENT_INFO } from "@/game/labels";
import { SHAPES, canPlace, createMealGame, currentHand, hasAnyMove, place, type MealState } from "@/game/puzzles/meal";
import type { Ingredient, MealParams, MealSubmission } from "@/game/puzzles/types";
import { Button } from "../ui/primitives";

export interface MealFinish {
  submission: MealSubmission;
  score: number;
  lines: number;
  maxCombo: number;
  themeCells: number;
}

interface Drag {
  p: number;
  cell: number;
  x: number;
  y: number;
  moved: boolean;
  startX: number;
  startY: number;
}

interface Popup {
  id: number;
  text: string;
  x: number;
  y: number;
  big: boolean;
}

const GHOST_LIFT = 56; // px: the dragged piece floats above the finger

function cellStyle(ing: Ingredient) {
  const info = INGREDIENT_INFO[ing];
  return {
    background: `radial-gradient(circle at 30% 25%, rgba(255,255,255,.75) 0 12%, transparent 13%), linear-gradient(160deg, ${info.color}, ${info.shade})`,
    boxShadow: `inset 0 -3px 0 rgba(0,0,0,.14), inset 0 0 0 1px rgba(255,255,255,.25)`,
  };
}

function shapeSize(p: number, params: MealParams) {
  const cells = SHAPES[params.pieces[p].shape];
  return { h: Math.max(...cells.map(([r]) => r)) + 1, w: Math.max(...cells.map(([, c]) => c)) + 1 };
}

/** Rows / columns that would be completed if piece p were placed at (r, c). */
function previewClears(state: MealState, p: number, r: number, c: number) {
  const { rows, cols } = state.params;
  const filled = state.board.map((row) => row.map((x) => x !== null));
  for (const [dr, dc] of SHAPES[state.params.pieces[p].shape]) filled[r + dr][c + dc] = true;
  const fullRows = new Set<number>();
  const fullCols = new Set<number>();
  for (let i = 0; i < rows; i++) if (filled[i].every(Boolean)) fullRows.add(i);
  for (let j = 0; j < cols; j++) if (filled.every((row) => row[j])) fullCols.add(j);
  return { fullRows, fullCols };
}

export function MealGame({ params, onFinish }: { params: MealParams; onFinish: (result: MealFinish) => void }) {
  const [game, setGame] = useState<MealState>(() => createMealGame(params));
  const [phase, setPhase] = useState<"ready" | "count" | "playing" | "over">("ready");
  const [count, setCount] = useState(3);
  const [elapsed, setElapsed] = useState(0);
  const [drag, setDrag] = useState<Drag | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [hover, setHover] = useState<{ r: number; c: number } | null>(null);
  const [flash, setFlash] = useState<Set<string>>(new Set());
  const [popups, setPopups] = useState<Popup[]>([]);
  const [comboBanner, setComboBanner] = useState<number>(0);

  const boardRef = useRef<HTMLDivElement>(null);
  const startRef = useRef(0);
  const popupId = useRef(0);
  const gameRef = useRef(game);
  useEffect(() => {
    gameRef.current = game;
  }, [game]);

  const hand = useMemo(() => currentHand(game), [game]);
  const limit = params.time_limit_ms;
  const remaining = Math.max(0, limit - elapsed);
  const greatChance = Math.min(0.35, 0.04 + game.score / 12000);

  /* ---------------- timing ---------------- */
  const startCountdown = () => {
    Sound.init();
    setCount(3);
    setPhase("count");
    Sound.tap();
    const timers = [1, 2].map((i) =>
      setTimeout(() => {
        setCount(3 - i);
        Sound.tap();
      }, i * 650),
    );
    timers.push(
      setTimeout(() => {
        startRef.current = performance.now();
        setPhase("playing");
        Sound.perfect();
      }, 3 * 650),
    );
  };

  const finish = useCallback(() => {
    setPhase("over");
    setDrag(null);
    setSelected(null);
    Sound.puzzleClear();
  }, []);

  useEffect(() => {
    if (phase !== "playing") return;
    let raf = 0;
    const tick = () => {
      const e = performance.now() - startRef.current;
      setElapsed(e);
      if (e >= limit) {
        finish();
        return;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [phase, limit, finish]);

  /* ---------------- geometry ---------------- */
  const cellFromPoint = useCallback(
    (x: number, y: number, p: number, lifted: boolean) => {
      const el = boardRef.current;
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const cell = rect.width / params.cols;
      const { h, w } = shapeSize(p, params);
      // anchor = top-left of the piece, which is centred horizontally on the finger and lifted above it
      const ax = x - (w * cell) / 2;
      const ay = lifted ? y - GHOST_LIFT - h * cell : y - (h * cell) / 2;
      const c = Math.round((ax - rect.left) / cell);
      const r = Math.round((ay - rect.top) / cell);
      if (r < -1 || c < -1 || r > params.rows || c > params.cols) return null;
      return { r, c };
    },
    [params],
  );

  const addPopup = useCallback((text: string, r: number, c: number, big = false) => {
    const id = ++popupId.current;
    setPopups((ps) => [...ps, { id, text, x: ((c + 0.5) / params.cols) * 100, y: ((r + 0.5) / params.rows) * 100, big }]);
    setTimeout(() => setPopups((ps) => ps.filter((p) => p.id !== id)), 900);
  }, [params]);

  const tryPlace = useCallback(
    (p: number, r: number, c: number) => {
      const state = gameRef.current;
      if (!canPlace(state, p, r, c)) {
        Sound.bad();
        return false;
      }
      const t = Math.round(performance.now() - startRef.current);
      const res = place(state, p, r, c, Math.min(t, limit));
      setGame(res.state);
      const lines = res.clearedRows.length + res.clearedCols.length;
      if (lines > 0) {
        setFlash(new Set(res.clearedCells.map((x) => `${x.r},${x.c}`)));
        setTimeout(() => setFlash(new Set()), 380);
        Sound.lineClear(lines);
        if (res.combo > 1) {
          Sound.combo(res.combo);
          setComboBanner(res.combo);
          setTimeout(() => setComboBanner(0), 900);
        }
        buzz(lines > 1 ? [20, 30, 20] : 18);
      } else {
        Sound.place();
      }
      const center = res.placedCells[Math.floor(res.placedCells.length / 2)];
      addPopup(`+${res.moveScore}`, center.r, center.c, lines > 0);
      if (!hasAnyMove(res.state)) setTimeout(finish, 450);
      return true;
    },
    [limit, addPopup, finish],
  );

  /* ---------------- pointer handling ---------------- */
  const dragRef = useRef<Drag | null>(null);

  // Listeners are attached synchronously on pointerdown so even very fast drags are tracked.
  const beginDrag = (p: number, e: React.PointerEvent) => {
    const cell = (boardRef.current?.getBoundingClientRect().width ?? 320) / params.cols;
    const first: Drag = { p, cell, x: e.clientX, y: e.clientY, startX: e.clientX, startY: e.clientY, moved: false };
    dragRef.current = first;
    setDrag(first);

    const move = (ev: PointerEvent) => {
      const cur = dragRef.current;
      if (!cur) return;
      const moved = cur.moved || Math.hypot(ev.clientX - cur.startX, ev.clientY - cur.startY) > 6;
      const next = { ...cur, x: ev.clientX, y: ev.clientY, moved };
      dragRef.current = next;
      setDrag(next);
      setHover(moved ? cellFromPoint(ev.clientX, ev.clientY, cur.p, true) : null);
    };
    const up = (ev: PointerEvent) => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("pointercancel", up);
      const cur = dragRef.current;
      dragRef.current = null;
      if (cur) {
        const moved = cur.moved || Math.hypot(ev.clientX - cur.startX, ev.clientY - cur.startY) > 6;
        if (moved) {
          const target = cellFromPoint(ev.clientX, ev.clientY, cur.p, true);
          if (target) tryPlace(cur.p, target.r, target.c);
          setSelected(null);
        } else {
          setSelected((s) => (s === cur.p ? null : cur.p));
        }
      }
      setDrag(null);
      setHover(null);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    window.addEventListener("pointercancel", up);
  };

  const onBoardTap = (r: number, c: number) => {
    if (phase !== "playing" || selected === null) return;
    if (tryPlace(selected, r, c)) setSelected(null);
  };

  /* ---------------- derived preview ---------------- */
  const activeP = drag?.moved ? drag.p : null;
  const preview = useMemo(() => {
    if (activeP === null || !hover || !canPlace(game, activeP, hover.r, hover.c)) return null;
    const cells = new Set(SHAPES[params.pieces[activeP].shape].map(([dr, dc]) => `${hover.r + dr},${hover.c + dc}`));
    return { cells, ...previewClears(game, activeP, hover.r, hover.c), ing: params.pieces[activeP].ingredient };
  }, [activeP, hover, game, params]);

  const submit = () => {
    onFinish({
      submission: { moves: game.moves, elapsed_ms: Math.round(Math.min(elapsed, limit)) },
      score: game.score,
      lines: game.lines,
      maxCombo: game.max_combo,
      themeCells: game.theme_cells,
    });
  };

  const theme = INGREDIENT_INFO[params.theme];

  return (
    <div className="flex select-none flex-col gap-3 touch-none">
      {/* HUD */}
      <div className="flex items-end justify-between px-1">
        <div>
          <div className="text-xs font-bold text-muted">
            テーマ：<span style={{ color: theme.shade }}>{theme.name}</span>
          </div>
          <div className="text-xs text-muted">おいしさ</div>
          <div className="font-mono text-3xl font-medium tabular leading-none">{game.score.toLocaleString("ja-JP")}</div>
        </div>
        <div className="text-right">
          <div className={`font-mono text-2xl tabular ${remaining < 5000 && phase === "playing" ? "text-eye" : ""}`}>
            {(remaining / 1000).toFixed(1)}
            <span className="text-sm">秒</span>
          </div>
          <div className="text-xs text-muted">ライン {game.lines}　最大コンボ {game.max_combo}</div>
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-line-soft">
        <div className="h-full rounded-full bg-gradient-to-r from-leaf to-banana transition-[width] duration-100" style={{ width: `${(remaining / limit) * 100}%` }} />
      </div>

      {/* board */}
      <div className="relative">
        <div
          ref={boardRef}
          className="grid aspect-square w-full gap-[3px] rounded-3xl bg-[#1e2c29]/85 p-[6px] shadow-[var(--shadow)]"
          style={{ gridTemplateColumns: `repeat(${params.cols}, 1fr)` }}
        >
          {game.board.map((row, r) =>
            row.map((ing, c) => {
              const key = `${r},${c}`;
              const inPreview = preview?.cells.has(key);
              const inLine = preview && (preview.fullRows.has(r) || preview.fullCols.has(c));
              const flashing = flash.has(key);
              return (
                <button
                  type="button"
                  key={key}
                  onClick={() => onBoardTap(r, c)}
                  aria-label={`${r + 1}行${c + 1}列`}
                  className={`relative rounded-[7px] transition-transform ${flashing ? "scale-110" : ""}`}
                  style={
                    ing
                      ? cellStyle(ing)
                      : inPreview && preview
                        ? { ...cellStyle(preview.ing), opacity: 0.55 }
                        : { background: inLine ? "rgba(255,213,74,.28)" : "rgba(255,255,255,.07)" }
                  }
                >
                  {ing && inLine && <span className="absolute inset-0 rounded-[7px] bg-white/45" />}
                  {flashing && <span className="absolute inset-0 rounded-[7px] bg-white motion-safe:animate-ping" />}
                </button>
              );
            }),
          )}
        </div>

        {popups.map((p) => (
          <span
            key={p.id}
            className={`pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 font-mono font-bold text-white drop-shadow float-up ${p.big ? "text-2xl text-banana" : "text-base"}`}
            style={{ left: `${p.x}%`, top: `${p.y}%` }}
          >
            {p.text}
          </span>
        ))}

        {comboBanner > 1 && (
          <div className="pointer-events-none absolute inset-x-0 top-[38%] text-center pop-in">
            <span className="rounded-2xl bg-eye px-4 py-1 font-kiwi text-2xl text-white shadow-lg">コンボ×{comboBanner}</span>
          </div>
        )}

        {phase !== "playing" && phase !== "over" && (
          <div className="absolute inset-0 grid place-items-center rounded-3xl bg-[#1e2c29]/55 backdrop-blur-[2px]">
            {phase === "ready" ? (
              <div className="text-center text-white">
                <p className="mb-3 text-sm leading-relaxed">
                  材料ブロックを置いて、
                  <br />
                  たて・よこの列をそろえて消そう。
                </p>
                <Button tone="banana" size="lg" onClick={startCountdown}>
                  スタート
                </Button>
              </div>
            ) : (
              <span key={count} className="font-mono text-7xl text-white pop-in">
                {count}
              </span>
            )}
          </div>
        )}
      </div>

      {/* great-success gauge */}
      <div className="flex items-center gap-2 px-1 text-xs font-bold text-muted">
        <span className="shrink-0">大成功ゲージ</span>
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-line-soft">
          <div className="h-full rounded-full bg-[linear-gradient(90deg,#7fc8ff,#ffd54a)] transition-[width] duration-500" style={{ width: `${(greatChance / 0.35) * 100}%` }} />
        </div>
        <span className="w-10 text-right font-mono tabular">{Math.round(greatChance * 100)}%</span>
      </div>

      {/* hand */}
      <div className="grid h-28 grid-cols-3 items-center gap-2 rounded-3xl border border-line-soft bg-surface-2 px-2">
        {hand.map((p) => {
          const placed = game.moves.some((m) => m.p === p);
          const { h, w } = shapeSize(p, params);
          const piece = params.pieces[p];
          const dragging = drag?.p === p && drag.moved;
          return (
            <button
              type="button"
              key={p}
              disabled={placed || phase !== "playing"}
              onPointerDown={(e) => {
                if (placed || phase !== "playing") return;
                e.preventDefault();
                beginDrag(p, e);
              }}
              className={`grid h-full place-items-center rounded-2xl transition ${selected === p ? "bg-tint-banana ring-2 ring-banana" : ""} ${placed || dragging ? "opacity-0" : ""}`}
              aria-label={`${INGREDIENT_INFO[piece.ingredient].name}のブロック`}
            >
              <div className="grid gap-[2px]" style={{ gridTemplateColumns: `repeat(${w}, 16px)`, gridTemplateRows: `repeat(${h}, 16px)` }}>
                {SHAPES[piece.shape].map(([dr, dc]) => (
                  <span key={`${dr}-${dc}`} className="rounded-[4px]" style={{ ...cellStyle(piece.ingredient), gridRow: dr + 1, gridColumn: dc + 1 }} />
                ))}
              </div>
            </button>
          );
        })}
      </div>

      {/* floating dragged piece */}
      {drag?.moved && <DragGhost p={drag.p} x={drag.x} y={drag.y} params={params} cell={drag.cell} />}

      {phase === "over" && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[#10201d]/60 p-6 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-[28px] bg-surface-2 p-6 text-center shadow-2xl pop-in">
            <div className="font-kiwi text-2xl">できあがり！</div>
            <div className="mt-1 text-sm text-muted">おいしさ</div>
            <div className="font-mono text-5xl tabular">{game.score.toLocaleString("ja-JP")}</div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
              <div className="rounded-2xl bg-tint-leaf py-2">
                <div className="text-xs text-muted">ライン</div>
                <div className="font-mono text-lg">{game.lines}</div>
              </div>
              <div className="rounded-2xl bg-tint-eye py-2">
                <div className="text-xs text-muted">最大コンボ</div>
                <div className="font-mono text-lg">{game.max_combo}</div>
              </div>
              <div className="rounded-2xl bg-tint-banana py-2">
                <div className="text-xs text-muted">{theme.name}</div>
                <div className="font-mono text-lg">{game.theme_cells}</div>
              </div>
            </div>
            <Button className="mt-5" block size="lg" onClick={submit}>
              ツユにあげる
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function DragGhost({ p, x, y, params, cell }: { p: number; x: number; y: number; params: MealParams; cell: number }) {
  const piece = params.pieces[p];
  const { h, w } = shapeSize(p, params);
  return (
    <div
      className="pointer-events-none fixed z-40 grid gap-[3px] drop-shadow-xl"
      style={{
        left: x - (w * cell) / 2,
        top: y - GHOST_LIFT - h * cell,
        gridTemplateColumns: `repeat(${w}, ${cell - 3}px)`,
        gridTemplateRows: `repeat(${h}, ${cell - 3}px)`,
      }}
    >
      {SHAPES[piece.shape].map(([dr, dc]) => (
        <span key={`${dr}-${dc}`} className="rounded-[7px]" style={{ ...cellStyle(piece.ingredient), gridRow: dr + 1, gridColumn: dc + 1 }} />
      ))}
    </div>
  );
}
