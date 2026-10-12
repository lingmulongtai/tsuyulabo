import { useEffect, useMemo } from "react";
import { Instances, type Instance } from "./Instances";
import { randomSource } from "./random";
import { surfaceTexture } from "./surfaces";
import { clamp01, type Habitat } from "./types";

export function Medium({ food, mould = 0 }: Habitat) {
  const moisture = clamp01(food?.moisture, 0.68), yeast = clamp01(food?.yeast, 0.5);
  const texture = useMemo(() => surfaceTexture("food", food?.color ?? "#bda45c"), [food?.color]);
  useEffect(() => () => texture.dispose(), [texture]);
  const speckles = useMemo(() => {
    const random = randomSource("yeast");
    return Array.from({ length: Math.round(360 * yeast) }, (): Instance => {
      const a = random() * 6.28, r = Math.sqrt(random()) * 0.99, s = 0.002 + random() ** 2 * 0.011;
      return { position: [Math.sin(a) * r, -1.066 + random() * 0.008, Math.cos(a) * r], scale: [s, s * 0.35, s], color: random() > 0.2 ? "#e6cf94" : "#8f713d" };
    });
  }, [yeast]);
  const colonies = useMemo(() => {
    const random = randomSource("mould");
    return Array.from({ length: Math.round(clamp01(mould, 0) * 160) }, (): Instance => {
      const patch = random() > 0.4 ? [-0.52, -0.48] : [0.5, 0.3];
      const a = random() * 6.28, r = random() * 0.22, s = 0.015 + random() * 0.02;
      return { position: [patch[0] + Math.cos(a) * r, -1.052, patch[1] + Math.sin(a) * r], scale: [s, s * 0.22, s], color: random() > 0.4 ? "#687259" : "#b4b393" };
    });
  }, [mould]);
  return <group>
    <mesh position={[0, -1.28, 0]} receiveShadow castShadow>
      <cylinderGeometry args={[1.055, 1.035, 0.41, 96, 4]} />
      <meshPhysicalMaterial map={texture} bumpMap={texture} bumpScale={0.018} roughness={0.83 - moisture * 0.5} clearcoat={moisture * 0.55} clearcoatRoughness={0.23} />
    </mesh>
    <Instances items={speckles}><sphereGeometry args={[1, 12, 8]} /><meshStandardMaterial roughness={0.86} /></Instances>
    <Instances items={colonies}><sphereGeometry args={[1, 8, 6]} /><meshStandardMaterial roughness={1} /></Instances>
  </group>;
}
