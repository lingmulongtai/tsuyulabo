import { useEffect, useMemo, useRef } from "react";
import type { ThreeEvent } from "@react-three/fiber";
import { CanvasTexture, DoubleSide } from "three";
import type { VivariumProps } from "./types";

/** Cylindrical mask erased in raycast UVs, independent of camera projection. */
export function GlassCare({ onGlassStroke, onGlassPick, wiped, grime = 0, mould = 0 }: Pick<VivariumProps, "onGlassStroke" | "onGlassPick" | "wiped"> & { grime?: number; mould?: number }) {
  const active = useRef<number | null>(null);
  const texture = useMemo(() => {
    const canvas = document.createElement("canvas"); canvas.width = 512; canvas.height = 512;
    return new CanvasTexture(canvas);
  }, []);
  useEffect(() => () => texture.dispose(), [texture]);
  useEffect(() => {
    const canvas = texture.image as HTMLCanvasElement, ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, 512, 512); ctx.fillStyle = `rgba(150,157,121,${Math.max(0, Math.min(1, grime)) * 0.7})`; ctx.fillRect(0, 0, 512, 512);
    ctx.fillStyle = "rgba(75,91,44,.7)";
    for (let i = 0; i < Math.round(Math.max(0, Math.min(1, mould)) * 25); i++) {
      ctx.beginPath(); ctx.arc((i * 137 + 53) % 512, (i * 193 + 71) % 512, 10 + i % 9, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalCompositeOperation = "destination-out";
    for (const p of wiped ?? []) { ctx.beginPath(); ctx.ellipse(p.u * 512, p.v * 512, 512 * 0.12, 512 * 0.12, 0, 0, Math.PI * 2); ctx.fill(); }
    ctx.globalCompositeOperation = "source-over";
    // Three requires a mutable upload flag after editing a canvas texture.
    // eslint-disable-next-line react-hooks/immutability
    texture.needsUpdate = true;
  }, [wiped, texture, grime, mould]);
  const stamp = (e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); if (e.uv) onGlassStroke?.(e.uv.x, 1 - e.uv.y); };
  return <mesh position={[0, 0.02, 0]} renderOrder={8}
    onPointerDown={e => {
      e.stopPropagation(); active.current = e.pointerId;
      (e.target as unknown as { setPointerCapture(id: number): void }).setPointerCapture(e.pointerId);
      if (onGlassPick) onGlassPick([e.point.x * 0.94, Math.max(-1, Math.min(1.15, e.point.y)), e.point.z * 0.94]);
      if (onGlassStroke) stamp(e);
    }}
    onPointerMove={e => { if (active.current === e.pointerId && onGlassStroke) stamp(e); }}
    onPointerUp={e => { active.current = null; (e.target as unknown as { releasePointerCapture(id: number): void }).releasePointerCapture(e.pointerId); }}
    onPointerCancel={() => { active.current = null; }}>
    <cylinderGeometry args={[1.075, 1.075, 2.26, 64, 1, true, -Math.PI / 2, Math.PI]} />
    <meshBasicMaterial map={wiped ? texture : undefined} transparent opacity={wiped ? 0.5 : 0} side={DoubleSide} depthWrite={false} />
  </mesh>;
}
