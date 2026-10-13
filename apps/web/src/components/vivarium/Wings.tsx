import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { CatmullRomCurve3, DataTexture, DoubleSide, Group, MeshPhysicalMaterial, RGBAFormat, ShaderChunk, Shape, ShapeGeometry, TubeGeometry, Vector3 } from "three";
import type { Pose } from "./controller";

export function Wings({ curly, vestigial, pose, unfold = 1 }: { curly: boolean; vestigial: boolean; pose: Pose; unfold?: number }) {
  const left = useRef<Group>(null), right = useRef<Group>(null);
  const thickness = useMemo(() => {
    const data = new Uint8Array(64 * 128 * 4);
    for (let y = 0; y < 128; y++) for (let x = 0; x < 64; x++) {
      const i = (y * 64 + x) * 4;
      data[i] = data[i + 1] = data[i + 2] = Math.round(50 + y * 1.2 + Math.sin(x * 0.09 + y * 0.02) * 25); data[i + 3] = 255;
    }
    const texture = new DataTexture(data, 64, 128, RGBAFormat); texture.needsUpdate = true; return texture;
  }, []);
  useEffect(() => () => thickness.dispose(), [thickness]);
  const membrane = useMemo(() => {
    const material = new MeshPhysicalMaterial({ color: "#eee9d9", side: DoubleSide, transparent: true, opacity: 0.13, depthWrite: false, metalness: 0, roughness: 0.31, ior: 1.52, iridescence: 0.65, iridescenceIOR: 1.36, iridescenceThicknessRange: [180, 620], iridescenceThicknessMap: thickness });
    material.onBeforeCompile = shader => {
      shader.fragmentShader = shader.fragmentShader.replace("#include <lights_physical_fragment>", ShaderChunk.lights_physical_fragment.replace("material.iridescence = iridescence;", "material.iridescence = iridescence * pow(1.0 - abs(dot(normal, normalize(vViewPosition))), 3.0);"));
      shader.fragmentShader = shader.fragmentShader.replace("#include <opaque_fragment>", "diffuseColor.a *= 0.45 + 2.8 * pow(1.0 - abs(dot(normal, normalize(vViewPosition))), 3.0);\n#include <opaque_fragment>");
    };
    material.customProgramCacheKey = () => "grazing-wing-v1";
    return material;
  }, [thickness]);
  useEffect(() => () => membrane.dispose(), [membrane]);
  const geometry = useMemo(() => {
    const outline = new Shape(); outline.moveTo(0, 0); outline.bezierCurveTo(0.16, -0.07, 0.29, -0.36, 0.22, -0.7); outline.bezierCurveTo(0.18, -0.94, -0.04, -0.94, -0.055, -0.66); outline.bezierCurveTo(-0.09, -0.35, -0.055, -0.08, 0, 0);
    const sheet = new ShapeGeometry(outline, 36);
    const pos = sheet.attributes.position;
    for (let i = 0; i < pos.count; i++) { const x = pos.getX(i), z = pos.getY(i); sheet.attributes.uv.setXY(i, (x + 0.1) / 0.4, -z / 0.94); pos.setXYZ(i, x, 0.01 + x * 0.03 + z * 0.1 + (curly ? z * z * 0.75 : z * z * 0.006), z); }
    sheet.computeVertexNormals();
    const paths = [[ [0,0],[0.06,-0.2],[0.14,-0.5],[0.15,-0.85] ], [[0,0],[0.015,-0.25],[0.02,-0.55],[0.01,-0.84]], [[0.05,-0.18],[0.17,-0.36],[0.23,-0.63]], [[0.025,-0.4],[0.12,-0.42],[0.19,-0.43]], [[0.025,-0.62],[0.09,-0.65],[0.2,-0.69]] ];
    const veins = paths.map(points => new TubeGeometry(new CatmullRomCurve3(points.map(([x,z]) => new Vector3(x, 0.012 + x * 0.03 + z * 0.1 + (curly ? z * z * 0.75 : z * z * 0.006), z))), 18, 0.0008, 4, false));
    return { sheet, veins };
  }, [curly]);
  useEffect(() => () => { geometry.sheet.dispose(); geometry.veins.forEach(g => g.dispose()); }, [geometry]);
  useFrame(() => {
    for (const [group, sign] of [[left.current, -1], [right.current, 1]] as const) if (group) {
      group.rotation.z = sign * pose.flight * (0.3 + Math.sin(pose.phase * 8) * 0.65);
      group.rotation.y = sign * (0.045 + pose.flight * 1.05);
    }
  }, -0.5);
  return <group position={[0, 0.225, -0.025]} scale={(vestigial ? 0.28 : 1) * (0.12 + 0.88 * unfold)}>
    {[-1, 1].map(sign => <group key={sign} ref={sign < 0 ? left : right} scale={[sign * 0.8, 1, 1]}>
      <mesh geometry={geometry.sheet} material={membrane} />
      {geometry.veins.map((vein,i) => <mesh key={i} geometry={vein}><meshStandardMaterial color="#736850" transparent opacity={0.42} roughness={0.7} /></mesh>)}
    </group>)}
  </group>;
}
