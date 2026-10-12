import { useEffect, useMemo } from "react";
import { Color, Float32BufferAttribute, LatheGeometry, Vector2 } from "three";
import { clamp01 } from "./types";
import { surfaceTexture } from "./surfaces";

export function Pupa({ age = 0.4 }: { age?: number }) {
  const maturity = clamp01(age, 0.4);
  const texture = useMemo(() => surfaceTexture("body"), []);
  useEffect(() => () => texture.dispose(), [texture]);
  const geometry = useMemo(() => {
    const g = new LatheGeometry(Array.from({ length: 101 }, (_, i) => {
      const t = i / 100, ridge = 1 + 0.01 * Math.cos(t * Math.PI * 22);
      return new Vector2(0.082 * Math.sin(t * Math.PI) ** 0.32 * ridge * (0.85 + t * 0.15), t * 0.39);
    }), 40);
    const colors = [];
    for (let i = 0; i < g.attributes.position.count; i++) {
      const t = g.attributes.position.getY(i) / 0.39;
      const x = g.attributes.position.getX(i), z = g.attributes.position.getZ(i);
      const mottling = Math.sin(x * 330 + t * 12) * Math.cos(z * 290 - t * 34) * 0.045;
      const c = new Color("#b77c3d").lerp(new Color("#322b21"), maturity * 0.9).multiplyScalar(0.93 + Math.cos(t * Math.PI * 22) * 0.035 + mottling); colors.push(c.r, c.g, c.b);
    }
    g.setAttribute("color", new Float32BufferAttribute(colors, 3)); return g;
  }, [maturity]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return <group rotation={[0.14, 0, -0.12]} scale={[1, 1, 0.8]}>
    <mesh geometry={geometry} castShadow><meshPhysicalMaterial vertexColors roughness={0.68} bumpMap={texture} bumpScale={0.003} clearcoat={0.04} transmission={0.04 * (1 - maturity)} thickness={0.08} /></mesh>
    {[-1, 1].map(sign => <mesh key={sign} position={[sign * 0.038, 0.399, 0]} rotation={[0, 0, sign * -0.3]}><coneGeometry args={[0.006, 0.04, 10]} /><meshStandardMaterial color="#785229" roughness={0.8} /></mesh>)}
  </group>;
}
