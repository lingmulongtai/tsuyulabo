import type { TrainingParams } from "../../src/game/puzzles/types";

/** Find a Hamiltonian path using only the public, server-issued checkpoints. */
export function solveTraining({ n, checkpoints }: Pick<TrainingParams, "n" | "checkpoints">): number[] {
  const ordered = [...checkpoints].sort((a, b) => a.k - b.k);
  const total = n * n;
  if (![5, 6].includes(n) || ordered.length < 2 ||
      new Set(ordered.map(cp => cp.cell)).size !== ordered.length ||
      ordered.some((cp, i) => cp.k !== i + 1 || !Number.isInteger(cp.cell) || cp.cell < 0 || cp.cell >= total)) {
    throw new Error("Invalid training checkpoints");
  }
  const neighbors = Array.from({ length: total }, (_, cell) => {
    const row = Math.floor(cell / n), col = cell % n;
    return [[row - 1, col], [row + 1, col], [row, col - 1], [row, col + 1]]
      .filter(([r, c]) => r >= 0 && c >= 0 && r < n && c < n)
      .map(([r, c]) => r * n + c);
  });
  const checkpoint = new Map(ordered.map(cp => [cp.cell, cp.k]));
  const end = ordered.at(-1)!.cell;
  const visited = Array<boolean>(total).fill(false);
  const path = [ordered[0].cell];
  visited[path[0]] = true;
  const deadline = Date.now() + 10_000;
  let nodes = 0;

  function viable(current: number) {
    // Every unused interior cell still needs an entrance and an exit.
    for (let cell = 0; cell < total; cell++) {
      if (visited[cell]) continue;
      const degree = neighbors[cell].filter(next => !visited[next] || next === current).length;
      if (degree < (cell === end ? 1 : 2)) return false;
    }
    // A path cannot recover an island separated by cells it already used.
    const reached = new Set([current]);
    const queue = [current];
    for (let i = 0; i < queue.length; i++) {
      for (const next of neighbors[queue[i]]) {
        if (!visited[next] && !reached.has(next)) { reached.add(next); queue.push(next); }
      }
    }
    return reached.size === total - path.length + 1;
  }

  function search(current: number, nextK: number): boolean {
    if (++nodes % 1024 === 0 && Date.now() > deadline) {
      throw new Error(`Training solver exceeded 10s: ${JSON.stringify({ n, checkpoints })}`);
    }
    if (path.length === total) return current === end && nextK === ordered.length + 1;
    if (!viable(current)) return false;
    const candidates = neighbors[current].filter(cell => !visited[cell] &&
      (!checkpoint.has(cell) || checkpoint.get(cell) === nextK) &&
      (cell !== end || path.length === total - 1));
    // Visit constrained cells first; backtrack when checkpoint order blocks that route.
    candidates.sort((a, b) => neighbors[a].filter(c => !visited[c]).length -
      neighbors[b].filter(c => !visited[c]).length);
    for (const cell of candidates) {
      visited[cell] = true;
      path.push(cell);
      if (search(cell, nextK + Number(checkpoint.has(cell)))) return true;
      path.pop();
      visited[cell] = false;
    }
    return false;
  }

  if (!search(path[0], 2)) throw new Error(`No training solution: ${JSON.stringify({ n, checkpoints })}`);
  return [...path];
}
