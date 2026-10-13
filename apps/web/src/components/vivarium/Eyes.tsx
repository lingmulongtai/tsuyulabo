import { useEffect, useMemo } from "react";
import { CanvasTexture, NoColorSpace, RepeatWrapping } from "three";

/** Hexagonal ommatidial lattice feeds the physical shader's bump and roughness. */
function facetTexture() {
  const canvas = document.createElement("canvas"); canvas.width = 512; canvas.height = 512;
  const ctx = canvas.getContext("2d")!; ctx.fillStyle = "#323232"; ctx.fillRect(0, 0, 512, 512);
  for (let row = -1; row < 36; row++) for (let col = -1; col < 31; col++) {
    const x = col * 18 + (row % 2) * 9, y = row * 15.6;
    ctx.beginPath();
    for (let k = 0; k < 6; k++) { const a = (k + 0.5) * Math.PI / 3; ctx.lineTo(x + Math.cos(a) * 9.7, y + Math.sin(a) * 9.7); }
    const gradient = ctx.createRadialGradient(x - 2, y - 2, 0, x, y, 10);
    gradient.addColorStop(0, "#eeeeee"); gradient.addColorStop(0.8, "#999999"); gradient.addColorStop(1, "#555555");
  ctx.fillStyle = gradient; ctx.fill();
  }
  const texture = new CanvasTexture(canvas); texture.colorSpace = NoColorSpace;
  texture.wrapS = texture.wrapT = RepeatWrapping; return texture;
}
export function Eyes({ white = false }: { white?: boolean }) {
  const facets = useMemo(() => facetTexture(), []);
  useEffect(() => () => facets.dispose(), [facets]);
  return <group>
    {[-1, 1].map(side => <mesh key={side} position={[side * 0.119, 0.109, 0.321]} rotation={[0.08, side * 0.3, side * -0.18]} scale={[0.055, 0.087, 0.079]}>
      <sphereGeometry args={[1, 48, 32]} />
      <meshPhysicalMaterial color={white ? "#e4dbc6" : "#b13213"} map={facets} roughness={0.78} bumpMap={facets} bumpScale={0.0017} clearcoat={0.015} clearcoatRoughness={0.6} />
    </mesh>)}
  </group>;
}
