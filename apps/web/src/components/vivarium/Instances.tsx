import { useLayoutEffect, useRef } from "react";
import { Color, InstancedMesh, Object3D } from "three";
import type { ReactNode } from "react";
import type {} from "@react-three/fiber";
import type { Point } from "./types";

export interface Instance { position: Point; scale: Point; rotation?: Point; color?: string }
/** One draw call per population; rebuild only when the environment/quality changes. */
export function Instances({ items, children, castShadow = false }: { items: Instance[]; children: ReactNode; castShadow?: boolean }) {
  const ref = useRef<InstancedMesh>(null);
  useLayoutEffect(() => {
    if (!ref.current) return;
    const object = new Object3D();
    items.forEach((item, i) => {
      object.position.set(...item.position); object.scale.set(...item.scale); object.rotation.set(...(item.rotation ?? [0, 0, 0])); object.updateMatrix();
      ref.current!.setMatrixAt(i, object.matrix);
      if (item.color) ref.current!.setColorAt(i, new Color(item.color));
    });
    ref.current.instanceMatrix.needsUpdate = true;
    if (ref.current.instanceColor) ref.current.instanceColor.needsUpdate = true;
    ref.current.computeBoundingSphere();
  }, [items]);
  return <instancedMesh ref={ref} args={[undefined, undefined, items.length]} castShadow={castShadow} receiveShadow>{children}</instancedMesh>;
}
