import { useEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { PerspectiveCamera, Vector3 } from "three";
import type { Point } from "./types";

export function CameraRig({ framing, focus, calm, paused, interactive = true, subject = "adult" }: { framing: "wide" | "close"; focus: Vector3; calm: boolean; paused: boolean; interactive?: boolean; subject?: "egg" | "larva" | "pupa" | "adult" }) {
  const controls = useRef<OrbitControlsImpl>(null);
  const camera = useThree(state => state.camera);
  const aspect = useThree(state => state.size.width / state.size.height);
  const previousFocus = useRef(new Vector3());
  const interacting = useRef(false);
  const initialized = useRef(false);
  useEffect(() => {
    const target = framing === "close" ? focus : new Vector3(0, -0.02, 0);
    const offset = new Vector3(...(!interactive ? [0, 0.4, 8] : framing === "close" ? [1.3, 0.85, 1.75] : [4.1, 2.3, 6.7]) as [number, number, number]);
    offset.multiplyScalar(Math.max(1, (framing === "wide" ? 0.75 : 0.6) / aspect));
    camera.position.copy(target).add(offset);
    if (camera instanceof PerspectiveCamera) {
      const fov = framing === "wide" ? 29 : { egg: 13, larva: 23, pupa: 21, adult: 29 }[subject];
      camera.setFocalLength(0.5 * camera.getFilmHeight() / Math.tan(fov * Math.PI / 360));
    }
    controls.current?.target.copy(target); camera.lookAt(target); controls.current?.update();
    previousFocus.current.copy(focus); initialized.current = true;
  }, [camera, framing, focus, subject, aspect, interactive]);
  useFrame((_, dt) => {
    if (!controls.current || !initialized.current) return;
    if (framing === "close" && !interacting.current) {
      const dx = focus.x - previousFocus.current.x, dy = focus.y - previousFocus.current.y, dz = focus.z - previousFocus.current.z;
      controls.current.target.add(new Vector3(dx, dy, dz)); camera.position.add(new Vector3(dx, dy, dz));
    }
    previousFocus.current.copy(focus);
    // Keep the macro lens outside the physical glass, including while orbiting near a wall.
    const radial = Math.hypot(camera.position.x, camera.position.z);
    if (camera.position.y < 1.95 && radial < 1.24) {
      const factor = 1.24 / Math.max(radial, 0.001);
      camera.position.set(camera.position.x * factor, camera.position.y, camera.position.z * factor);
    }
    controls.current.autoRotate = interactive && !calm && !paused && !interacting.current && framing === "wide";
    controls.current.autoRotateSpeed = 0.13 * Math.min(dt * 60, 3);
  });
  const target: Point = [0, -0.02, 0];
  return <OrbitControls ref={controls} makeDefault enabled={interactive} target={target} enablePan={false} enableDamping dampingFactor={0.08} minDistance={1.45} maxDistance={16} minPolarAngle={0.2} maxPolarAngle={Math.PI * 0.48} autoRotateSpeed={0.13} onStart={() => { interacting.current = true; }} onEnd={() => { interacting.current = false; }} />;
}
