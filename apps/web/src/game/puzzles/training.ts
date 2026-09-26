import type { Stars, TrainingParams, TrainingSubmission, TrainingVerifyResult } from "./types";

export interface TrainingState {
  readonly params: TrainingParams;
  readonly path: readonly number[];
}

export function cellToRC(n: number, cell: number): { r: number; c: number } {
  return { r: Math.floor(cell / n), c: cell % n };
}

export function rcToCell(n: number, r: number, c: number): number {
  return r * n + c;
}

function inBounds(n: number, cell: number): boolean {
  return Number.isInteger(cell) && cell >= 0 && cell < n * n;
}

/** Orthogonal neighbors in up, right, down, left order (never wrapping a row). */
export function neighbors(n: number, cell: number): number[] {
  if (!inBounds(n, cell)) return [];
  const { r, c } = cellToRC(n, cell);
  return [[r - 1, c], [r, c + 1], [r + 1, c], [r, c - 1]]
    .filter(([rr, cc]) => rr >= 0 && rr < n && cc >= 0 && cc < n)
    .map(([rr, cc]) => rcToCell(n, rr, cc));
}

export function createTrainingGame(params: TrainingParams): TrainingState {
  return { params, path: [] };
}

/** Invalid steps are no-ops; stepping onto the preceding cell undoes one step. */
export function tryStep(state: TrainingState, cell: number): TrainingState {
  const { params, path } = state;
  if (!inBounds(params.n, cell)) return state;
  const checkpoint = params.checkpoints.find((cp) => cp.cell === cell);
  if (path.length === 0) return checkpoint?.k === 1 ? { params, path: [cell] } : state;
  if (cell === path.at(-1)) return state;
  if (path.length > 1 && cell === path.at(-2)) return { params, path: path.slice(0, -1) };
  if (path.includes(cell) || !neighbors(params.n, path[path.length - 1]).includes(cell)) return state;
  const nextK = params.checkpoints.filter((cp) => path.includes(cp.cell)).length + 1;
  if (checkpoint && checkpoint.k !== nextK) return state;
  return { params, path: [...path, cell] };
}

/** Keep the selected visited cell as the new endpoint; unknown cells are no-ops. */
export function truncateTo(state: TrainingState, cell: number): TrainingState {
  const index = state.path.indexOf(cell);
  return index < 0 || index === state.path.length - 1
    ? state : { params: state.params, path: state.path.slice(0, index + 1) };
}

export function isSolved(state: TrainingState): boolean {
  return verifyTraining(state.params, { path: state.path, elapsed_ms: 0 }).valid;
}

export function starsFor(n: number, elapsedMs: number): Stars {
  const scale = n * n / 25;
  return elapsedMs < 12000 * scale ? 3 : elapsedMs < 25000 * scale ? 2 : 1;
}

/** Validate the submitted path directly: replaying pointer edits would hide revisits. */
export function verifyTraining(
  params: TrainingParams, submission: TrainingSubmission,
): TrainingVerifyResult {
  const { path, elapsed_ms } = submission;
  const { n, checkpoints } = params;
  if (!Number.isFinite(elapsed_ms) || elapsed_ms < 0) {
    return { valid: false, reason: "non_monotonic_time" };
  }
  if (path.length !== n * n) return { valid: false, reason: "wrong_length" };
  if (path.some((cell) => !inBounds(n, cell))) return { valid: false, reason: "out_of_bounds" };
  if (new Set(path).size !== path.length) return { valid: false, reason: "revisit" };
  if (path[0] !== checkpoints.find((cp) => cp.k === 1)?.cell) {
    return { valid: false, reason: "bad_start" };
  }
  const lastK = Math.max(...checkpoints.map((cp) => cp.k));
  if (path.at(-1) !== checkpoints.find((cp) => cp.k === lastK)?.cell) {
    return { valid: false, reason: "bad_end" };
  }
  let nextK = 1;
  for (let i = 0; i < path.length; i++) {
    if (i > 0 && !neighbors(n, path[i - 1]).includes(path[i])) {
      return { valid: false, reason: "not_adjacent" };
    }
    const checkpoint = checkpoints.find((cp) => cp.cell === path[i]);
    if (checkpoint) {
      if (checkpoint.k !== nextK) return { valid: false, reason: "checkpoint_order" };
      nextK++;
    }
  }
  return { valid: true, stars: starsFor(n, elapsed_ms) };
}
