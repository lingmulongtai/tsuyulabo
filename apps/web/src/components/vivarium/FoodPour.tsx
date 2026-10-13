import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import type { Group } from "three";

export function FoodPour({ color, paused, calm }: { color?: string; paused: boolean; calm: boolean }) {
  const group = useRef<Group>(null), elapsed = useRef(0);
  useFrame((_, dt) => {
    if (!group.current || paused) return;
    elapsed.current += Math.min(dt, 0.05);
    const t = Math.min(1, elapsed.current / (calm ? 0.3 : 2.5));
    group.current.visible = t < 1;
    group.current.position.y = 1.2 - t * 2.25;
    group.current.scale.set(0.9 + t * 0.1, Math.max(0.02, 0.5 * Math.sin(t * Math.PI)), 1);
  }, -0.5);
  return <group ref={group} position={[0, 1.2, 0]}>
    <mesh><cylinderGeometry args={[0.045, 0.13, 1.8, 12]} /><meshStandardMaterial color={color ?? "#bda45c"} roughness={0.45} /></mesh>
  </group>;
}
