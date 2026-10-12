import { useEffect, useMemo } from "react";
import { Color, Float32BufferAttribute, SphereGeometry } from "three";
import { randomSource } from "./random";
import { surfaceTexture } from "./surfaces";

/** Tapered mesonotum with a raised dorsal arch and muted longitudinal markings. */
export function Thorax({ color }: { color: string }) {
  const texture = useMemo(() => surfaceTexture("body", color), [color]);
  useEffect(() => () => texture.dispose(), [texture]);
  const geometry = useMemo(() => {
    const geometry = new SphereGeometry(1, 48, 32), p = geometry.attributes.position, random = randomSource("mesonotum");
    const colors = [];
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
      const taper = 0.87 + 0.13 * (z + 1) * 0.5;
      p.setXYZ(i, x * 0.157 * taper, y * 0.145 + 0.012 * (1 - z * z) + z * 0.012, z * 0.21);
      const stripe = y > 0.3 ? Math.exp(-(((Math.abs(x) - 0.35) / 0.11) ** 2)) * 0.18 : 0;
      const c = new Color(color).multiplyScalar(0.87 + random() * 0.14 - stripe); colors.push(c.r, c.g, c.b);
    }
    geometry.setAttribute("color", new Float32BufferAttribute(colors, 3)); geometry.computeVertexNormals(); return geometry;
  }, [color]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return <mesh geometry={geometry} position={[0, 0.095, 0]} castShadow><meshPhysicalMaterial vertexColors bumpMap={texture} bumpScale={0.0012} roughness={0.49} clearcoat={0.08} clearcoatRoughness={0.5} /></mesh>;
}
