"use client";

import { useId } from "react";
import { edgePath, edgeWidth, layoutGroups, rateGlow } from "./layout";
import { CIRCUITS, type BrainActivity } from "./types";

export function BrainDiagram({ activity, frame, selected, onSelect }: {
  activity: BrainActivity; frame: number; selected: string; onSelect: (name: string) => void;
}) {
  const id = useId();
  const layout = layoutGroups(activity.groups);
  const nodes = new Map(layout.nodes.map((node) => [node.name, node]));
  return (
    <div className="overflow-x-auto rounded-2xl border border-line-soft bg-surface-2" tabIndex={0} role="region" aria-label="脳の回路図。左右にスクロールできます">
      <svg viewBox={`0 0 ${layout.width} ${layout.height}`} className="w-full min-w-[620px]" aria-label="細胞群を選ぶと発火率を確認できます">
        <defs>
          <marker id={`${id}-excitatory`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 Z" fill="var(--leaf)" />
          </marker>
          <marker id={`${id}-inhibitory`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 8 0 L 8 10" stroke="var(--eye)" strokeWidth="2" />
          </marker>
        </defs>
        {["感覚入力", "介在ニューロン", "行動への出力"].map((title, index) => (
          <text key={title} x={120 + index * 240} y="26" textAnchor="middle" fill="var(--muted)" fontSize="16">{title}</text>
        ))}
        {layout.bands.map((band, index) => (
          <g key={band.circuit}>
            <rect x="8" y={band.y} width="704" height={band.height - 8} rx="18" fill={index % 2 ? "var(--surface)" : "var(--tint-leaf)"} />
            <text x="24" y={band.y + 22} fill="var(--muted)" fontSize="14">{CIRCUITS[band.circuit] ?? band.circuit}</text>
          </g>
        ))}
        <text x="24" y={layout.modulatorY + 22} fill="var(--ai)" fontSize="14">学習を調節する DAN（PAM / PPL1）</text>
        {activity.edges.map((edge) => {
          const pre = nodes.get(edge.pre_group), post = nodes.get(edge.post_group);
          if (!pre || !post) return null;
          return (
            <path key={`${edge.pre_group}-${edge.post_group}`} d={edgePath(pre, post)} fill="none"
              stroke={edge.sign === "excitatory" ? "var(--leaf)" : "var(--eye)"}
              strokeWidth={edgeWidth(edge.weight_sum)} strokeDasharray={edge.sign === "inhibitory" ? "6 4" : undefined}
              opacity="0.55" markerEnd={`url(#${id}-${edge.sign})`}>
              <title>{edge.pre_group} → {edge.post_group}：{edge.sign === "excitatory" ? "興奮" : "抑制"}、重み合計 {edge.weight_sum.toFixed(1)}</title>
            </path>
          );
        })}
        {layout.nodes.map((node) => {
          const rate = node.rates[frame] ?? 0;
          const glow = rateGlow(rate);
          const color = node.kind === "modulatory" ? "var(--ai)" : "var(--leaf)";
          return (
            <g key={node.name} transform={`translate(${node.x} ${node.y})`} role="button" tabIndex={0}
              aria-label={`${node.name}、${rate.toFixed(1)} Hz`} aria-pressed={selected === node.name}
              onClick={() => onSelect(node.name)} onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(node.name); }
              }} className="cursor-pointer">
              <title>{node.name}：{rate.toFixed(1)} Hz</title>
              <circle r={25 + glow * 9} fill={color} opacity={glow * 0.24} />
              <circle r="20" fill="var(--surface-2)" stroke={selected === node.name ? "var(--banana)" : color} strokeWidth={selected === node.name ? 4 : 2} />
              <circle r="17" fill={color} opacity={0.08 + glow * 0.85} />
              <text y="5" textAnchor="middle" fill="var(--ink)" fontSize="11" fontFamily="monospace" pointerEvents="none">{Math.round(rate)}</text>
              <text y="42" textAnchor="middle" fill="var(--ink)" fontSize="14" fontFamily="monospace">{node.name}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
