import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { BufferGeometry, Float32BufferAttribute, Color, InstancedMesh, Mesh, MeshPhysicalMaterial, Object3D } from "three";
import type { Pose } from "./controller";
import type { Stage } from "./types";

const rings = 96, sides = 24;
function radius(t: number) {
  return (0.01 + Math.sin(Math.PI * t) ** 0.48 * 0.045) * (1 + Math.cos(t * Math.PI * 24) * 0.025);
}
/** A continuous cuticle avoids intersecting transparent segment surfaces. */
export function Larva({ pose, stage }: { pose: Pose; stage: Stage }) {
  const segments = useRef<InstancedMesh>(null);
  const lastPhase = useRef<number | null>(null);
  const organColors = useMemo(() => [new Color("#9b8965"), new Color("#c4b38b"), new Color("#f9f3e0")], []);
  const scratch = useRef(new Object3D());
  const cuticle = useRef<Mesh>(null);
  const skin = useMemo(() => {
    const geometry = new BufferGeometry(), vertices = [], indices = [];
    for (let i = 0; i <= rings; i++) for (let j = 0; j <= sides; j++) {
      const t = i / rings, a = j / sides * Math.PI * 2;
      vertices.push(Math.cos(a) * radius(t), Math.sin(a) * radius(t) * 0.72 - 0.04, (t - 0.5) * 0.56);
      if (i < rings && j < sides) { const p = i * (sides + 1) + j; indices.push(p, p + 1, p + sides + 1, p + 1, p + sides + 2, p + sides + 1); }
    }
    geometry.setAttribute("position", new Float32BufferAttribute(vertices, 3)); geometry.setIndex(indices); geometry.computeVertexNormals();
    const material = new MeshPhysicalMaterial({ color: "#f5f0e0", roughness: 0.42, transmission: 0.55, thickness: 0.025, ior: 1.36, attenuationColor: "#edd29b", attenuationDistance: 0.7, transparent: true, opacity: 0.94, depthWrite: false });
    // Forward-scattering rim supplements volume absorption at phone budgets.
    material.onBeforeCompile = shader => {
      shader.fragmentShader = shader.fragmentShader.replace("#include <opaque_fragment>", "outgoingLight += vec3(0.14, 0.10, 0.055) * pow(1.0 - abs(dot(normal, normalize(vViewPosition))), 3.0);\n#include <opaque_fragment>");
    };
    return { geometry, material };
  }, []);
  useEffect(() => () => { skin.geometry.dispose(); skin.material.dispose(); }, [skin]);
  useFrame(() => {
    if (!cuticle.current || lastPhase.current === pose.phase) return;
    lastPhase.current = pose.phase;
    const strength = Math.min(1, pose.speed * 30 + pose.burrow * 0.4);
    const positions = cuticle.current.geometry.attributes.position;
    for (let i = 0; i <= rings; i++) {
      const t = i / rings, wave = Math.sin(pose.phase * 1.7 - t * 7) * strength, r = radius(t) * (1 + wave * 0.06);
      for (let j = 0; j <= sides; j++) {
        const a = j / sides * Math.PI * 2;
        positions.setXYZ(i * (sides + 1) + j, Math.cos(a) * r + Math.sin(pose.phase * 0.65 - t * 2) * 0.009 * strength, Math.sin(a) * r * 0.72 - 0.04 + Math.max(0, wave) * 0.01, (t - 0.5) * 0.56 + wave * 0.006);
      }
    }
    positions.needsUpdate = true; cuticle.current.geometry.computeVertexNormals();
    if (segments.current) {
      const object = scratch.current;
      let index = 0;
      for (let i = 0; i < 12; i++) {
        const wave = Math.sin(pose.phase * 1.7 - i * 0.63) * strength;
        const x = Math.sin(pose.phase * 0.65 - i * 0.21) * 0.012;
        const y = -0.035 + Math.max(0, wave) * 0.014, z = (i - 5) * 0.043 + wave * 0.008;
        const width = 0.027 + Math.sin((i + 1) / 13 * Math.PI) * 0.028;
        object.position.set(x, y, z); object.scale.set(width * 0.2, 0.008, (i === 0 || i === 11 ? 0.009 : 0.025) * (1 + wave * 0.11)); object.updateMatrix();
        segments.current.setMatrixAt(index, object.matrix); segments.current.setColorAt(index++, organColors[i < 3 ? 0 : 1]);
        if (i > 1 && i < 10) for (const sign of [-1, 1]) {
          object.position.set(x + sign * width * 0.43, y + 0.007, z); object.scale.set(0.0009, 0.0009, 0.0225); object.updateMatrix();
          segments.current.setMatrixAt(index, object.matrix); segments.current.setColorAt(index++, organColors[2]);
        }
      }
      segments.current.instanceMatrix.needsUpdate = true;
      if (segments.current.instanceColor) segments.current.instanceColor.needsUpdate = true;
    }
  }, -0.5);
  return <group scale={stage === "larva1" ? 0.55 : stage === "larva2" ? 0.78 : 1}>
    <instancedMesh ref={segments} args={[undefined, undefined, 28]} frustumCulled={false}>
      <sphereGeometry args={[1, 10, 6]} /><meshStandardMaterial roughness={0.8} />
    </instancedMesh>
    <mesh ref={cuticle} geometry={skin.geometry} material={skin.material} castShadow />
    {[-1, 1].map(sign => <mesh key={sign} position={[sign * 0.006, -0.045, 0.281]} rotation={[1.1, 0, sign * 0.2]}><coneGeometry args={[0.004, 0.015, 7]} /><meshStandardMaterial color="#211d14" roughness={0.8} /></mesh>)}
  </group>;
}
