import type {
  Ingredient, InvalidReason, MealMove, MealParams, MealScore, MealSubmission,
  MealVerifyResult, Shape,
} from "./types";

export const SHAPES: Readonly<Record<Shape, readonly (readonly [number, number])[]>> = {
  m1: [[0, 0]], d2h: [[0, 0], [0, 1]], d2v: [[0, 0], [1, 0]],
  i3h: [[0, 0], [0, 1], [0, 2]], i3v: [[0, 0], [1, 0], [2, 0]],
  l3a: [[0, 0], [1, 0], [1, 1]], l3b: [[0, 0], [0, 1], [1, 0]],
  l3c: [[0, 0], [0, 1], [1, 1]], l3d: [[0, 1], [1, 0], [1, 1]],
  o4: [[0, 0], [0, 1], [1, 0], [1, 1]],
  i4h: [[0, 0], [0, 1], [0, 2], [0, 3]], i4v: [[0, 0], [1, 0], [2, 0], [3, 0]],
  t4: [[0, 0], [0, 1], [0, 2], [1, 1]], l4: [[0, 0], [1, 0], [2, 0], [2, 1]],
  s4: [[0, 1], [0, 2], [1, 0], [1, 1]],
  i5h: [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]],
  i5v: [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]],
  o9: [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]],
};

export interface MealCell {
  readonly r: number;
  readonly c: number;
  readonly ingredient: Ingredient;
}
export interface MealState extends MealScore {
  readonly params: MealParams;
  readonly board: readonly (readonly (Ingredient | null)[])[];
  readonly moves: readonly MealMove[];
  readonly combo: number;
}
export interface MealPlacement {
  readonly state: MealState;
  readonly placedCells: readonly MealCell[];
  readonly clearedRows: readonly number[];
  readonly clearedCols: readonly number[];
  readonly clearedCells: readonly MealCell[];
  readonly moveScore: number;
  readonly combo: number;
}

export function createMealGame(params: MealParams): MealState {
  return {
    params, board: Array.from({ length: params.rows }, () =>
      Array<Ingredient | null>(params.cols).fill(null)),
    moves: [], score: 0, lines: 0, max_combo: 0, theme_cells: 0, combo: 0,
  };
}

/** Piece indices, in deal order; a new hand appears only when the old one is exhausted. */
export function currentHand(state: MealState): number[] {
  const { hand_size, pieces } = state.params;
  const start = Math.floor(state.moves.length / hand_size) * hand_size;
  const used = new Set(state.moves.map(({ p }) => p));
  return Array.from({ length: Math.min(hand_size, pieces.length - start) }, (_, i) => start + i)
    .filter((p) => !used.has(p));
}

function placementReason(state: MealState, p: number, r: number, c: number): InvalidReason | null {
  if (state.moves.some((move) => move.p === p)) return "already_placed";
  if (!Number.isInteger(p) || !currentHand(state).includes(p)) return "not_in_hand";
  const { rows, cols, pieces } = state.params;
  const cells = SHAPES[pieces[p].shape].map(([dr, dc]) => [r + dr, c + dc]);
  if (!Number.isInteger(r) || !Number.isInteger(c) ||
    cells.some(([rr, cc]) => rr < 0 || rr >= rows || cc < 0 || cc >= cols)) {
    return "out_of_bounds";
  }
  return cells.some(([rr, cc]) => state.board[rr][cc] !== null) ? "cell_occupied" : null;
}

export function canPlace(state: MealState, p: number, r: number, c: number): boolean {
  return placementReason(state, p, r, c) === null;
}

export class MealMoveError extends Error {
  constructor(public readonly reason: InvalidReason) {
    super(reason);
    this.name = "MealMoveError";
  }
}

/** Throws MealMoveError on an illegal move; the input state is never changed. */
export function place(state: MealState, p: number, r: number, c: number, t: number): MealPlacement {
  const previousT = state.moves.at(-1)?.t ?? 0;
  if (!Number.isFinite(t) || t < previousT) throw new MealMoveError("non_monotonic_time");
  if (t > state.params.time_limit_ms + 1500) throw new MealMoveError("time_exceeded");
  const reason = placementReason(state, p, r, c);
  if (reason) throw new MealMoveError(reason);
  const { params } = state;
  const piece = params.pieces[p];
  const board = state.board.map((row) => [...row]);
  const placedCells = SHAPES[piece.shape].map(([dr, dc]) => ({
    r: r + dr, c: c + dc, ingredient: piece.ingredient,
  }));
  for (const cell of placedCells) board[cell.r][cell.c] = cell.ingredient;
  // Detect both axes before clearing either, and collect their union once.
  const clearedRows = board.flatMap((row, i) => row.every((cell) => cell !== null) ? [i] : []);
  const clearedCols = Array.from({ length: params.cols }, (_, i) => i)
    .filter((col) => board.every((row) => row[col] !== null));
  const clearedCells: MealCell[] = [];
  for (let rr = 0; rr < params.rows; rr++) {
    for (let cc = 0; cc < params.cols; cc++) {
      const ingredient = board[rr][cc];
      if (ingredient !== null && (clearedRows.includes(rr) || clearedCols.includes(cc))) {
        clearedCells.push({ r: rr, c: cc, ingredient });
        board[rr][cc] = null;
      }
    }
  }
  const lines = clearedRows.length + clearedCols.length;
  const combo = lines > 0 ? state.combo + 1 : 0;
  const multiplier = combo > 0 ? 1 + 0.5 * (combo - 1) : 0;
  const themeCells = clearedCells.filter((cell) => cell.ingredient === params.theme).length;
  const moveScore = placedCells.length + Math.floor(100 * lines * (lines + 1) / 2 * multiplier)
    + themeCells * 15;
  return {
    state: {
      params, board, moves: [...state.moves, { p, r, c, t }], combo,
      score: state.score + moveScore, lines: state.lines + lines,
      max_combo: Math.max(state.max_combo, combo), theme_cells: state.theme_cells + themeCells,
    },
    placedCells, clearedRows, clearedCols, clearedCells, moveScore, combo,
  };
}

export function hasAnyMove(state: MealState): boolean {
  return currentHand(state).some((p) => state.board.some((row, r) =>
    row.some((_, c) => canPlace(state, p, r, c))));
}

/** The UI stops at the actual limit; the replay verifier alone allows delivery grace. */
export function isOver(state: MealState, elapsedMs: number): boolean {
  return elapsedMs >= state.params.time_limit_ms || !hasAnyMove(state);
}

export function verifyMeal(params: MealParams, submission: MealSubmission): MealVerifyResult {
  if (!Number.isFinite(submission.elapsed_ms) || submission.elapsed_ms < 0) {
    return { valid: false, reason: "non_monotonic_time" };
  }
  let state = createMealGame(params);
  try {
    for (const { p, r, c, t } of submission.moves) state = place(state, p, r, c, t).state;
  } catch (error) {
    if (error instanceof MealMoveError) return { valid: false, reason: error.reason };
    throw error;
  }
  if (submission.elapsed_ms < (state.moves.at(-1)?.t ?? 0)) {
    return { valid: false, reason: "non_monotonic_time" };
  }
  const { score, lines, max_combo, theme_cells } = state;
  return { valid: true, score, lines, max_combo, theme_cells };
}
