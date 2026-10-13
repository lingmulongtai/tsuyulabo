import { useEffect, useMemo } from "react";
import { FrontSide, Vector2 } from "three";
import { Instances, type Instance } from "./Instances";
import { randomSource } from "./random";
import { surfaceTexture } from "./surfaces";
import { budgets } from "./quality";
import { clamp01, type Quality, type VivariumProps } from "./types";
import { glassWiped } from "./glass-wiping";

const profile = [[0,-1.59],[0.94,-1.59],[1.06,-1.56],[1.12,-1.48],[1.13,-1.36],[1.13,1.42],[1.15,1.48],[1.15,1.56],[1.09,1.59],[1.065,1.54],[1.065,1.46],[1.07,-1.35],[1.02,-1.47],[0,-1.48]].map(([x,y]) => new Vector2(x,y));
const plugProfile = [[0,1.48],[0.95,1.48],[1.035,1.52],[1.055,1.59],[1.055,1.76],[1.015,1.82],[0.9,1.84],[0,1.84]].map(([x,y]) => new Vector2(x,y));
export function Vial({ humidity = 0.65, grime = 0, quality, wiped }: { humidity?: number; grime?: number; quality: Quality; wiped?: VivariumProps["wiped"] }) {
  const maps = useMemo(() => ({ glass: surfaceTexture("glass"), cotton: surfaceTexture("cotton") }), []);
  useEffect(() => () => { maps.glass.dispose(); maps.cotton.dispose(); }, [maps]);
  const drops = useMemo(() => {
    const random = randomSource("condensation");
    return Array.from({ length: Math.round(budgets[quality].droplets * clamp01(humidity, 0.65) ** 1.5) }, (): Instance => {
      const angle = random() * Math.PI * 2, radius = 0.008 + random() ** 3 * 0.039;
      return { position: [Math.sin(angle) * 1.058, -0.85 + random() * 2.23, Math.cos(angle) * 1.058], scale: [radius, radius * (1.1 + random()), radius * 0.65], rotation: [0, angle, 0] };
    }).filter(drop => !wiped || !glassWiped(drop.position, wiped));
  }, [humidity, quality, wiped]);
  const fibers = useMemo(() => {
    const random = randomSource("plug");
    return Array.from({ length: 130 }, (): Instance => {
      const angle = random() * 6.28, radius = Math.sqrt(random());
      return { position: [Math.sin(angle) * radius, 1.66 + random() * 0.18, Math.cos(angle) * radius], scale: [0.006, 0.04 + random() * 0.07, 0.006], rotation: [random() * 3, random() * 3, random() * 3], color: random() > 0.5 ? "#ded8c2" : "#b4b2a3" };
    });
  }, []);
  return <group>
    <mesh renderOrder={5}>
      <latheGeometry args={[profile, quality === "low" ? 64 : 128]} />
      <meshPhysicalMaterial color="#e9efdf" metalness={0} roughness={0.075 + (wiped ? 0 : clamp01(grime, 0)) * 0.36} roughnessMap={maps.glass} transmission={1} thickness={0.018} ior={1.48} transparent opacity={0.42} envMapIntensity={1.3} side={FrontSide} depthWrite={false} />
    </mesh>
    <mesh>
      <latheGeometry args={[plugProfile, 96]} />
      <meshStandardMaterial color="#f6f3e9" map={maps.cotton} bumpMap={maps.cotton} bumpScale={0.018} roughness={1} />
    </mesh>
    <Instances items={fibers}><cylinderGeometry args={[0.3, 0.6, 1, 3]} /><meshStandardMaterial roughness={1} /></Instances>
    <Instances items={drops}>
      <sphereGeometry args={[1, 12, 8]} />
      <meshPhysicalMaterial color="#e4eee5" transmission={0.96} roughness={0.04} thickness={0.06} ior={1.333} transparent opacity={0.65} depthWrite={false} />
    </Instances>
  </group>;
}
