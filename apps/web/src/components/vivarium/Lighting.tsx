import { Environment } from "@react-three/drei";
import type { Quality } from "./types";

export function Lighting({ quality }: { quality: Quality }) {
  return <>
    <Environment files="/vivarium/studio.hdr" environmentIntensity={0.65} />
    <ambientLight intensity={0.25} color="#e9ddc2" />
    <directionalLight position={[-3, 5, 2]} color="#ffe0b6" intensity={2.2} castShadow={quality !== "low"} shadow-radius={3} shadow-mapSize={quality === "high" ? [2048, 2048] : [1024, 1024]} shadow-bias={-0.0003} shadow-normalBias={0.006} shadow-camera-left={-2} shadow-camera-right={2} shadow-camera-top={2} shadow-camera-bottom={-2} shadow-camera-near={0.1} shadow-camera-far={15} />
    <directionalLight position={[3, 1, 3]} color="#c4d2de" intensity={0.65} />
    <spotLight position={[0, 3, -4]} color="#ffedce" intensity={25} angle={0.6} penumbra={1} distance={12} />
    <mesh position={[0, -1.6, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[200, 200]} /><meshStandardMaterial color="#373b30" roughness={0.92} />
    </mesh>
  </>;
}
