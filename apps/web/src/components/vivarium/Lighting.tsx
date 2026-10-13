import { Environment } from "@react-three/drei";
import type { Quality } from "./types";

export function Lighting({ quality }: { quality: Quality }) {
  return <>
    <Environment files="/vivarium/studio.hdr" environmentIntensity={0.38} />
    <ambientLight intensity={0.12} color="#e9ddc2" />
    {/* Inverse-square irradiance, with distances in mm: intensity scales as mm². */}
    <spotLight position={[-65,125,85]} color="#ffe0ac" intensity={60000} decay={2} distance={550} angle={0.7} penumbra={0.8} castShadow={quality !== "low"} shadow-radius={3} shadow-mapSize={quality === "high" ? [2048,2048] : [1024,1024]} shadow-bias={-0.00005} shadow-normalBias={0.04} shadow-camera-near={5} shadow-camera-far={300} />
    <directionalLight position={[90,65,45]} color="#c1d9ee" intensity={0.85} />
    <pointLight position={[15,95,-65]} color="#ffebc9" intensity={13000} decay={2} distance={350} />
  </>;
}
