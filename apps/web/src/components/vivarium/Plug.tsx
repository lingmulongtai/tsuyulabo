import { useEffect, useMemo } from "react";
import { Vector2 } from "three";
import { Instances, type Instance } from "./Instances";
import { randomSource } from "./random";
import { surfaceTexture } from "./surfaces";
import type { Quality } from "./types";

const profile = [[0,87],[10.5,87],[11.6,89],[11.8,94],[12.1,97],[11.6,102],[10.8,104],[8,104.7],[0,104.9]].map(([x,y]) => new Vector2(x,y));
/** Compressed cotton core plus tangled surface fibres, all dimensions in mm. */
export function Plug({ quality }: { quality: Quality }) {
  const cotton = useMemo(() => surfaceTexture("cotton"), []);
  useEffect(() => () => cotton.dispose(), [cotton]);
  const fibers = useMemo(() => {
    const random = randomSource("cotton-fibres");
    return Array.from({ length: quality === "high" ? 1700 : quality === "medium" ? 800 : 200 }, (): Instance => {
      const a = random() * Math.PI * 2, top = random() > 0.55;
      const r = top ? Math.sqrt(random()) * 11.5 : 11.7 + random() * 0.35;
      return { position: [Math.sin(a) * r, top ? 104.3 + random() * 0.5 : 94 + random() * 9, Math.cos(a) * r], scale: [0.016 + random() * 0.014, 0.3 + random() * 1.2, 0.016], rotation: [random() * 3, random() * 3, random() * 3], color: random() > 0.35 ? "#ece7da" : "#c2beb0" };
    });
  }, [quality]);
  return <group>
    <mesh castShadow><latheGeometry args={[profile, 64]} /><meshStandardMaterial color="#eee9dd" map={cotton} bumpMap={cotton} bumpScale={0.28} roughness={1} /></mesh>
    <Instances items={fibers}><cylinderGeometry args={[0.4, 0.6, 1, 3]} /><meshStandardMaterial roughness={1} /></Instances>
  </group>;
}
