import { useEffect, useMemo } from "react";
import { BufferGeometry, CylinderGeometry, Float32BufferAttribute } from "three";
import { Instances, type Instance } from "./Instances";
import { randomSource } from "./random";
import { surfaceTexture } from "./surfaces";
import { vialMM } from "./scale";
import { clamp01, type Habitat } from "./types";

/** Millimetre relief: wet wall meniscus, shallow burrows and irregular meal surface. */
export function foodHeight(x: number, z: number) {
  const r = Math.hypot(x, z);
  const meniscus = 0.65 * Math.exp(-Math.max(0, vialMM.innerRadius - r) / 0.32);
  const uneven = 0.045 * Math.sin(x * 2.3 + Math.sin(z * 1.7)) * Math.cos(z * 2.7) + 0.025 * Math.sin(x * 8 + z * 5);
  const tunnel = -0.18 * Math.exp(-(((z - 2.5 * Math.sin(x * 0.45) - 3) / 0.23) ** 2)) * Math.exp(-((x / 7) ** 6));
  const pit = -0.32 * Math.exp(-((x + 2.1) ** 2 + (z - 1.5) ** 2) / 0.16);
  return vialMM.food + meniscus + uneven + tunnel + pit;
}

export function foodSurfaceGeometry() {
    const g = new BufferGeometry(), positions = [], uv = [], indices = [];
    const rings = 64, sides = 128;
    for (let i = 0; i <= rings; i++) for (let j = 0; j <= sides; j++) {
      const r = i / rings * vialMM.innerRadius, a = j / sides * Math.PI * 2;
      const x = Math.cos(a) * r, z = Math.sin(a) * r;
      positions.push(x, foodHeight(x, z), z); uv.push(x / 23.6 + 0.5, z / 23.6 + 0.5);
      if (i < rings && j < sides) { const k = i * (sides + 1) + j; indices.push(k, k + 1, k + sides + 1, k + 1, k + sides + 2, k + sides + 1); }
    }
    g.setAttribute("position", new Float32BufferAttribute(positions, 3));
    g.setAttribute("uv", new Float32BufferAttribute(uv, 2)); g.setIndex(indices); g.computeVertexNormals(); return g;
}

export function Medium({ food, mould = 0 }: Habitat) {
  const moisture = clamp01(food?.moisture, 0.68), yeast = clamp01(food?.yeast, 0.5);
  const texture = useMemo(() => surfaceTexture("food", food?.color ?? "#bda45c"), [food?.color]);
  const top = useMemo(() => foodSurfaceGeometry(), []);
  const side = useMemo(() => {
    const g = new CylinderGeometry(11.8, 11.55, 20, 96, 1, true), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const y = p.getY(i) > 0 ? foodHeight(p.getX(i), p.getZ(i)) : 1.5;
      p.setY(i, y);
    }
    g.computeVertexNormals(); return g;
  }, []);
  useEffect(() => () => side.dispose(), [side]);
  useEffect(() => () => { texture.dispose(); }, [texture]);
  useEffect(() => () => top.dispose(), [top]);
  const speckles = useMemo(() => {
    const random = randomSource("yeast");
    return Array.from({ length: Math.round(520 * yeast) }, (): Instance => {
      const a = random() * 6.28, r = Math.sqrt(random()) * 11.65, s = 0.025 + random() ** 2 * 0.075;
      const x = Math.sin(a) * r, z = Math.cos(a) * r;
      return { position: [x, foodHeight(x, z) + s * 0.3, z], scale: [s, s * 0.65, s * 0.8], rotation: [0, a, random()], color: random() > 0.2 ? "#cfc09a" : "#8f754b" };
    });
  }, [yeast]);
  const colonies = useMemo(() => {
    const random = randomSource("mould");
    return Array.from({ length: Math.round(clamp01(mould, 0) * 160) }, (): Instance => {
      const patch = random() > 0.4 ? [-6, -5] : [5, 3];
      const a = random() * 6.28, r = random() * 2.2, s = 0.12 + random() * 0.2;
      const x = patch[0] + Math.cos(a) * r, z = patch[1] + Math.sin(a) * r;
      return { position: [x, foodHeight(x, z) + 0.04, z], scale: [s, s * 0.22, s], color: random() > 0.4 ? "#687259" : "#b4b393" };
    });
  }, [mould]);
  return <group>
    <mesh geometry={side} receiveShadow castShadow>
      <meshPhysicalMaterial map={texture} bumpMap={texture} bumpScale={0.05} roughness={0.76} sheen={0.3} sheenColor="#cdb583" sheenRoughness={1} />
    </mesh>
    <mesh geometry={top} receiveShadow castShadow>
      <meshPhysicalMaterial map={texture} bumpMap={texture} bumpScale={0.012} roughnessMap={texture} roughness={0.95 - moisture * 0.45} clearcoat={moisture * 0.3} clearcoatRoughnessMap={texture} clearcoatRoughness={0.35} />
    </mesh>
    <Instances items={speckles}><sphereGeometry args={[1, 8, 6]} /><meshStandardMaterial roughness={0.92} /></Instances>
    <Instances items={colonies}><sphereGeometry args={[1, 8, 6]} /><meshStandardMaterial roughness={1} /></Instances>
  </group>;
}
