import { useMemo } from "react";
import { Euler, Quaternion, Vector3 } from "three";
import { Instances, type Instance } from "./Instances";
import { randomSource } from "./random";
import { budgets } from "./quality";
import type { Quality } from "./types";

export function Bristles({ quality, seed }: { quality: Quality; seed: string }) {
  const hairs = useMemo(() => {
    const random = randomSource(seed + "hairs");
    return Array.from({ length: budgets[quality].hairs }, (_, i): Instance => {
      const angle = random() * Math.PI * 2, lat = Math.acos(0.2 + random() * 0.8);
      const head = i % 5 === 0;
      const x = Math.sin(lat) * Math.cos(angle), y = Math.cos(lat), z = Math.sin(lat) * Math.sin(angle);
      const normal = new Vector3(x * 0.8, y, z * 0.65 - 0.4).normalize();
      const length = 0.009 + random() ** 7 * 0.105;
      const position = new Vector3(x * (head ? 0.115 : 0.145), 0.102 + y * (head ? 0.135 : 0.147), z * (head ? 0.09 : 0.207) + (head ? 0.294 : 0)).addScaledVector(normal, length * 0.45);
      const rotation = new Euler().setFromQuaternion(new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), normal));
      return { position: [position.x, position.y, position.z], scale: [0.0011, length, 0.0011], rotation: [rotation.x, rotation.y, rotation.z] };
    });
  }, [quality, seed]);
  return <Instances items={hairs}><coneGeometry args={[1, 1, 3]} /><meshStandardMaterial color="#2a251b" roughness={0.95} /></Instances>;
}
