import { useEffect, useMemo } from "react";
import { MeshTransmissionMaterial } from "@react-three/drei";
import { FrontSide, Vector2 } from "three";
import { Instances, type Instance } from "./Instances";
import { Plug } from "./Plug";
import { randomSource } from "./random";
import { surfaceTexture } from "./surfaces";
import { budgets } from "./quality";
import { fromMillimetres } from "./scale";
import { clamp01, type Quality, type VivariumProps } from "./types";
import { glassWiped } from "./glass-wiping";

// Outer shell and rolled mouth: thickness supplies the inner optical interface.
// A bounded offscreen buffer includes translucent organisms, avoiding native nested-transmission loss.
const profile = [[0,0],[10.6,0],[12.1,0.5],[12.5,1.5],[12.5,93],[12.7,94],[12.7,94.6],[12.3,95],[11.8,94.8],[11.7,94],[11.8,92.8]].map(([x,y]) => new Vector2(x,y));
export function Vial({ humidity = 0.65, grime = 0, quality, wiped }: { humidity?: number; grime?: number; quality: Quality; wiped?: VivariumProps["wiped"] }) {
  const glass = useMemo(() => surfaceTexture("glass"), []);
  useEffect(() => () => glass.dispose(), [glass]);
  const drops = useMemo(() => {
    const random = randomSource("condensation-clusters");
    return Array.from({ length: Math.round(budgets[quality].droplets * clamp01(humidity, 0.65) ** 1.5) }, (_, i): Instance => {
      const cluster = i % 7, angle = cluster * 2.399 + (random() - 0.5) * 0.4;
      const radius = 0.055 + random() ** 3 * 0.33;
      const y = 59 + cluster * 4 + (random() - 0.5) * 9;
      return { position: [Math.sin(angle) * 11.72, y, Math.cos(angle) * 11.72], scale: [radius, radius * (1.1 + random()), radius * 0.4], rotation: [0, angle, 0] };
    }).filter(drop => !wiped || !glassWiped(fromMillimetres(drop.position), wiped));
  }, [humidity, quality, wiped]);
  return <group>
    <mesh renderOrder={5}>
      <latheGeometry args={[profile, quality === "low" ? 64 : 96]} />
      {quality === "low" ? <meshPhysicalMaterial color="#e8eee8" roughness={0.12} transparent opacity={0.1} depthWrite={false} /> :
        <MeshTransmissionMaterial color="#f5f8f2" samples={quality === "high" ? 3 : 1} resolution={1024} backside={false} chromaticAberration={0.002} anisotropicBlur={0} distortion={0} temporalDistortion={0} roughness={0.0008 + (wiped ? 0 : clamp01(grime, 0)) * 0.012} roughnessMap={glass} transmission={1} thickness={0.7} ior={1.48} transparent envMapIntensity={0.8} side={FrontSide} depthWrite={false} />}
    </mesh>
    <Plug quality={quality} />
    <Instances items={drops}>
      <sphereGeometry args={[1, 10, 6]} />
      <meshPhysicalMaterial color="#eef4f0" clearcoat={1} roughness={0.06} ior={1.333} transparent opacity={0.65} depthWrite={false} />
    </Instances>
  </group>;
}
