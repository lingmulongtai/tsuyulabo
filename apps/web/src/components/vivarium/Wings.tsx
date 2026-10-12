import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { CatmullRomCurve3, DataTexture, DoubleSide, Group, RGBAFormat, Shape, ShapeGeometry, TubeGeometry, Vector3 } from "three";
import type { Pose } from "./controller";

export function Wings({ curly, vestigial, pose }: { curly: boolean; vestigial: boolean; pose: Pose }) {
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
  const geometry = useMemo(() => {
    const outline = new Shape(); outline.moveTo(0, 0); outline.bezierCurveTo(0.16, -0.07, 0.29, -0.36, 0.22, -0.7); outline.bezierCurveTo(0.18, -0.94, -0.04, -0.94, -0.055, -0.66); outline.bezierCurveTo(-0.09, -0.35, -0.055, -0.08, 0, 0);
    const sheet = new ShapeGeometry(outline, 36);
    const pos = sheet.attributes.position;
    for (let i = 0; i < pos.count; i++) { const x = pos.getX(i), z = pos.getY(i); sheet.attributes.uv.setXY(i, (x + 0.1) / 0.4, -z / 0.94); pos.setXYZ(i, x, 0.01 + x * 0.06 + (curly ? z * z * 0.75 : z * z * 0.025), z); }
    sheet.computeVertexNormals();
    const paths = [[ [0,0],[0.06,-0.2],[0.14,-0.5],[0.15,-0.85] ], [[0,0],[0.015,-0.25],[0.02,-0.55],[0.01,-0.84]], [[0.05,-0.18],[0.17,-0.36],[0.23,-0.63]], [[0.025,-0.4],[0.12,-0.42],[0.19,-0.43]], [[0.025,-0.62],[0.09,-0.65],[0.2,-0.69]] ];
    const veins = paths.map(points => new TubeGeometry(new CatmullRomCurve3(points.map(([x,z]) => new Vector3(x, 0.014 + x * 0.06 + (curly ? z * z * 0.75 : z * z * 0.025), z))), 18, 0.0011, 5, false));
    return { sheet, veins };
  }, [curly]);
  useEffect(() => () => { geometry.sheet.dispose(); geometry.veins.forEach(g => g.dispose()); }, [geometry]);
  useFrame(() => {
    for (const [group, sign] of [[left.current, -1], [right.current, 1]] as const) if (group) {
      group.rotation.z = sign * pose.flight * (0.3 + Math.sin(pose.phase * 8) * 0.65);
      group.rotation.y = sign * (0.2 + pose.flight * 0.9);
    }
  });
  return <group position={[0, 0.23, -0.025]} scale={vestigial ? 0.28 : 1}>
    {[-1, 1].map(sign => <group key={sign} ref={sign < 0 ? left : right} scale={[sign, 1, 1]}>
      <mesh geometry={geometry.sheet}>
        <meshPhysicalMaterial color="#ddd9c9" side={DoubleSide} transparent opacity={0.5} depthWrite={false} metalness={0.22} roughness={0.18} transmission={0.15} thickness={0.001} ior={1.52} iridescence={1} iridescenceIOR={1.36} iridescenceThicknessRange={[180, 620]} iridescenceThicknessMap={thickness} />
      </mesh>
      {geometry.veins.map((vein,i) => <mesh key={i} geometry={vein}><meshStandardMaterial color="#736850" transparent opacity={0.72} roughness={0.7} /></mesh>)}
    </group>)}
  </group>;
}
