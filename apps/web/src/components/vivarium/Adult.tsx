import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Color, Float32BufferAttribute, LatheGeometry, Mesh, Vector2 } from "three";
import { Eyes } from "./Eyes";
import { Wings } from "./Wings";
import { Bristles } from "./Bristles";
import { Legs } from "./Legs";
import { Thorax } from "./Thorax";
import { surfaceTexture } from "./surfaces";
import type { Pose } from "./controller";
import type { Phenotype, Quality } from "./types";

export function Adult({ pose, sex, traits, quality, seed }: { pose: Pose; sex: "f" | "m"; traits: readonly Phenotype[]; quality: Quality; seed: string }) {
  const proboscis = useRef<Mesh>(null);
  const abdomenMesh = useRef<Mesh>(null);
  const yellow = traits.includes("yellow"), ebony = traits.includes("ebony");
  const bodyColor = ebony ? "#38332b" : yellow ? "#d2ae42" : "#977044";
  const texture = useMemo(() => surfaceTexture("body", bodyColor), [bodyColor]);
  const abdomen = useMemo(() => {
    const male = sex === "m";
    const points = Array.from({ length: 65 }, (_, i) => {
      const t = i / 64;
      return new Vector2(Math.sin(Math.PI * t) ** (male ? 0.6 : 0.8) * (0.145 + 0.025 * t) * (1 + Math.sin(t * Math.PI * 12) * 0.035), t * (male ? 0.48 : 0.59));
    });
    const g = new LatheGeometry(points, 48); const colors: number[] = [];
    const positions = g.attributes.position;
    for (let i = 0; i < positions.count; i++) {
      const t = positions.getY(i) / (male ? 0.48 : 0.59);
      const theta = Math.atan2(positions.getX(i), positions.getZ(i));
      const dark = ((t * 6 + Math.sin(theta * 3) * 0.08) % 1 < 0.3 && positions.getZ(i) > -0.04) || (male && t > 0.67);
      const c = new Color(dark ? ebony ? "#181a17" : "#3e2f22" : bodyColor).multiplyScalar(0.95 + Math.sin(theta * 7 + t * 85) * 0.04); colors.push(c.r, c.g, c.b);
    }
    g.setAttribute("color", new Float32BufferAttribute(colors, 3)); return g;
  }, [sex, bodyColor, ebony]);
  useEffect(() => () => { abdomen.dispose(); texture.dispose(); }, [abdomen, texture]);
  useFrame(() => {
    if (proboscis.current) { proboscis.current.scale.y = 0.3 + pose.feed * 1.9; proboscis.current.position.y = -0.012 - pose.feed * 0.035; }
    if (abdomenMesh.current) abdomenMesh.current.scale.x = 1 + Math.sin(pose.phase * 0.71) * Math.sin(pose.phase * 0.13) * 0.012;
  });
  return <group scale={0.58}>
    <mesh ref={abdomenMesh} position={[0, 0.065, -0.13]} rotation={[-Math.PI / 2, 0, 0]} geometry={abdomen} castShadow>
      <meshStandardMaterial vertexColors roughness={0.76} bumpMap={texture} bumpScale={0.004} />
    </mesh>
    <Thorax color={bodyColor} />
    <mesh position={[0, 0.095, 0.294]} scale={[0.151, 0.136, 0.116]} castShadow>
      <sphereGeometry args={[1, 32, 24]} /><meshStandardMaterial color={ebony ? "#39392e" : "#c39b5e"} roughness={0.73} />
    </mesh>
    <Eyes white={traits.includes("white")} />
    <Wings curly={traits.includes("curly")} vestigial={traits.includes("vestigial")} pose={pose} />
    <Bristles quality={quality} seed={seed} />
    <Legs pose={pose} male={sex === "m"} />
    <mesh ref={proboscis} position={[0, -0.01, 0.369]} rotation={[-0.4, 0, 0]}><capsuleGeometry args={[0.022, 0.06, 4, 8]} /><meshStandardMaterial color="#6b4930" roughness={0.65} /></mesh>
    {[-1, 1].map(side => <group key={side} position={[side * 0.047, 0.12, 0.41]}>
      <mesh scale={[0.027, 0.035, 0.022]}><sphereGeometry args={[1, 12, 8]} /><meshStandardMaterial color="#816334" roughness={0.8} /></mesh>
      <mesh position={[side * 0.025, 0.04, 0.015]} rotation={[0.4, 0, side * -0.7]}><cylinderGeometry args={[0.001, 0.003, 0.12, 4]} /><meshStandardMaterial color="#342f21" /></mesh>
      <mesh position={[side * 0.15, -0.005, -0.55]} scale={[0.021, 0.02, 0.022]}><sphereGeometry args={[1, 12, 8]} /><meshStandardMaterial color="#c2a477" /></mesh>
    </group>)}
  </group>;
}
