import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { InstancedMesh, Object3D, Vector3 } from "three";
import type { Pose } from "./controller";

const up = new Vector3(0, 1, 0);
export function Legs({ pose, male }: { pose: Pose; male: boolean }) {
  const ref = useRef<InstancedMesh>(null);
  const scratch = useRef({ object: new Object3D(), a: new Vector3(), b: new Vector3(), dir: new Vector3() });
  useFrame(() => {
    if (!ref.current) return;
    const { object, a, b, dir } = scratch.current;
    for (let leg = 0; leg < 6; leg++) {
      const side = leg < 3 ? -1 : 1, pair = leg % 3;
      const cycle = pose.phase + (leg % 2 ? Math.PI : 0);
      const stride = Math.min(1, pose.speed * 7);
      const z = 0.17 - pair * 0.16;
      const lift = Math.max(0, Math.sin(cycle)) * 0.12 * stride;
      const grooming = pair === 0 ? pose.groom : 0;
      const tipX = side * (0.35 - grooming * 0.29 - pose.flight * 0.1);
      const tipY = -0.15 + lift + grooming * (0.33 + Math.sin(pose.phase * 3) * 0.04) + pose.flight * 0.1;
      const tipZ = z + (1 - pair) * 0.19 + Math.cos(cycle) * 0.12 * stride + grooming * 0.14;
      const points = [[side * 0.09, 0.08, z], [side * 0.24, 0.065 + lift * 0.4, z + (1 - pair) * 0.13], [tipX, tipY + 0.055, tipZ], [tipX + side * 0.055, tipY, tipZ + 0.03]];
      for (let segment = 0; segment < 3; segment++) {
        a.fromArray(points[segment]); b.fromArray(points[segment + 1]);
        dir.subVectors(b, a); const length = dir.length(); object.position.copy(a).add(b).multiplyScalar(0.5);
        object.quaternion.setFromUnitVectors(up, dir.normalize());
        object.scale.set(segment === 0 ? 0.008 : 0.0035, length, segment === 0 ? 0.008 : 0.0035);
        object.updateMatrix(); ref.current.setMatrixAt(leg * 3 + segment, object.matrix);
      }
      // Short tibial/femoral setae follow each articulated segment in the same draw.
      for (let hair = 0; hair < 18; hair++) {
        const segment = Math.floor(hair / 6), t = (hair % 6 + 0.5) / 6;
        a.fromArray(points[segment]); b.fromArray(points[segment + 1]);
        object.position.copy(a).lerp(b, t);
        object.position.x += side * 0.004;
        object.rotation.set(0.5, 0, side * -0.9);
        object.scale.set(0.0008, 0.015 + (hair % 3) * 0.004, 0.0008); object.updateMatrix();
        ref.current.setMatrixAt(60 + leg * 18 + hair, object.matrix);
      }
      // Male sex combs on the first tarsus, following the animated foreleg.
      for (let tooth = 0; tooth < 7; tooth++) {
        object.position.set(tipX + side * tooth * 0.004, tipY + 0.015, tipZ + 0.014);
        object.rotation.set(0, 0, side * 0.6); object.scale.set(0.002, male && pair === 0 ? 0.021 : 0, 0.002); object.updateMatrix();
        ref.current.setMatrixAt(18 + leg * 7 + tooth, object.matrix);
      }
    }
    ref.current.instanceMatrix.needsUpdate = true;
  }, -0.5);
  return <instancedMesh ref={ref} args={[undefined, undefined, 168]} frustumCulled={false} castShadow>
    <cylinderGeometry args={[0.6, 1, 1, 5]} /><meshStandardMaterial color="#594127" roughness={0.8} />
  </instancedMesh>;
}
