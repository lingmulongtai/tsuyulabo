import { canPlace, currentHand, place, type MealState } from "../../src/game/puzzles/meal";
import type { CleaningParams, PupationSiteParams, TemperatureParams } from "../../src/game/puzzles/types";

/** Prefer clears, then dense rows/columns and connected space for the next hand. */
export function nextMealMove(state: MealState) {
  let best: { p: number; r: number; c: number; value: number } | undefined;
  for (const p of currentHand(state)) {
    for (let r = 0; r < state.params.rows; r++) {
      for (let c = 0; c < state.params.cols; c++) {
        if (!canPlace(state, p, r, c)) continue;
        const result = place(state, p, r, c, 0);
        const board = result.state.board;
        const rows = board.map(row => row.filter(Boolean).length);
        const cols = board[0].map((_, col) => board.filter(row => row[col]).length);
        let isolated = 0;
        for (let y = 0; y < board.length; y++) {
          for (let x = 0; x < board[y].length; x++) {
            if (board[y][x]) continue;
            if ([[y - 1, x], [y + 1, x], [y, x - 1], [y, x + 1]]
              .every(([rr, cc]) => rr < 0 || cc < 0 || rr >= board.length || cc >= board[0].length || board[rr][cc])) isolated++;
          }
        }
        const value = result.moveScore * 3 + [...rows, ...cols].reduce((sum, n) => sum + n * n, 0)
          - isolated * 35 - (r + c) * 0.01;
        if (!best || value > best.value) best = { p, r, c, value };
      }
    }
  }
  return best;
}

/** Alternating crossings of the triangle wave's target, kept under two seconds where possible. */
export function cleaningTimes(params: CleaningParams): number[] {
  const phases = [params.zone.center / 2, 1 - params.zone.center / 2];
  const times = Array.from({ length: 6 }, (_, cycle) => phases.map(phase =>
    Math.round((cycle + phase - params.phase) * params.period_ms)))
    .flat().filter(t => t >= 80).sort((a, b) => a - b);
  return times.slice(0, params.taps);
}

export function temperatureTime(params: TemperatureParams): number {
  const angle = Math.asin((25 - params.center_c) / params.amp_c) / (2 * Math.PI);
  return Math.min(...[angle, 0.5 - angle].map(phase => {
    let cycles = phase - params.phase;
    while (cycles * params.period_ms < 80) cycles++;
    return Math.round(cycles * params.period_ms);
  }));
}

// The hint is public but only 70% reliable. Never read the server's secret winning_id.
export function hintedSite(params: PupationSiteParams) {
  const pattern = params.hint.includes("乾いた") ? /乾|えさから離/ :
    params.hint.includes("しめった") ? /しめ|しっとり/ : /風|光/;
  const option = params.options.find(option => pattern.test(option.detail));
  if (!option) throw new Error(`Unrecognized pupation hint: ${params.hint}`);
  return option;
}
