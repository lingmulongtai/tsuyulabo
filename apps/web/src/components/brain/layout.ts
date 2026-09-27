import { CIRCUITS, type ActivityGroup, type GroupKind } from "./types";

export interface NodePosition { x: number; y: number }
export interface PlacedGroup extends ActivityGroup, NodePosition {}
const COLUMNS: Record<GroupKind, number> = { sensory: 120, inter: 360, output: 600, modulatory: 360 };
const ORDER = ["PN", "KC", "APL"];

export function layoutGroups(groups: ActivityGroup[]) {
  const nodes: PlacedGroup[] = [];
  const bands: { circuit: string; y: number; height: number }[] = [];
  const circuits = [...new Set(groups.map((group) => group.circuit))].sort((a, b) => {
    const order = Object.keys(CIRCUITS);
    return order.indexOf(a) - order.indexOf(b) || a.localeCompare(b);
  });
  let y = 42;
  for (const circuit of circuits) {
    const row = groups.filter((group) => group.circuit === circuit && group.kind !== "modulatory");
    let rows = 1;
    for (const kind of ["sensory", "inter", "output"] as const) {
      const column = row.filter((group) => group.kind === kind).sort((a, b) =>
        ORDER.indexOf(a.name) - ORDER.indexOf(b.name) || a.name.localeCompare(b.name),
      );
      rows = Math.max(rows, column.length);
      column.forEach((group, index) => nodes.push({ ...group, x: COLUMNS[kind], y: y + 54 + index * 76 }));
    }
    const height = rows * 76 + 38;
    bands.push({ circuit, y, height });
    y += height;
  }
  const modulators = groups.filter((group) => group.kind === "modulatory").sort((a, b) => a.name.localeCompare(b.name));
  modulators.forEach((group, index) => nodes.push({ ...group, x: 240 + (index % 2) * 240, y: y + 62 + Math.floor(index / 2) * 76 }));
  return { nodes, bands, width: 720, height: y + (modulators.length ? 110 + Math.floor((modulators.length - 1) / 2) * 76 : 12), modulatorY: y };
}

export function edgePath(pre: NodePosition, post: NodePosition): string {
  if (pre.x === post.x) {
    const bend = pre.y < post.y ? 70 : -70;
    return `M ${pre.x + Math.sign(bend) * 18} ${pre.y} C ${pre.x + bend} ${pre.y}, ${post.x + bend} ${post.y}, ${post.x + Math.sign(bend) * 24} ${post.y}`;
  }
  const direction = Math.sign(post.x - pre.x);
  const middle = (pre.x + post.x) / 2;
  return `M ${pre.x + direction * 22} ${pre.y} C ${middle} ${pre.y}, ${middle} ${post.y}, ${post.x - direction * 27} ${post.y}`;
}

export function edgeWidth(weight: number): number {
  return 1 + Math.min(4, Math.log1p(Math.abs(weight)) / 2);
}

export function rateGlow(rate: number): number {
  return Math.max(0, Math.min(1, rate / 200));
}
