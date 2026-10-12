import { useEffect, useMemo } from "react";
import { CatmullRomCurve3, TubeGeometry, Vector3 } from "three";

export function Egg() {
  const filaments = useMemo(() => [-1, 1].map(sign => new TubeGeometry(new CatmullRomCurve3([new Vector3(sign * 0.018, 0.012, 0.077), new Vector3(sign * 0.03, 0.073, 0.1), new Vector3(sign * 0.048, 0.105, 0.125), new Vector3(sign * 0.06, 0.105, 0.145)]), 24, 0.002, 8, false)), []);
  useEffect(() => () => filaments.forEach(g => g.dispose()), [filaments]);
  return <group position={[0, -0.052, 0]} rotation={[0, -0.5, 0.08]}>
    <mesh scale={[0.037, 0.031, 0.104]} castShadow><sphereGeometry args={[1, 40, 24]} /><meshPhysicalMaterial color="#f2e9ce" roughness={0.52} transmission={0.02} thickness={0.035} /></mesh>
    {filaments.map((g, i) => <mesh geometry={g} key={i}><meshStandardMaterial color="#e4dec8" roughness={0.8} /></mesh>)}
  </group>;
}
