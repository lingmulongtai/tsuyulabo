import { useEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { PerspectiveCamera, Vector3 } from "three";

const wideTarget = new Vector3(0, 62, 0);
export function CameraRig({ framing, focus, calm, paused, interactive = true, subject = "adult", composition = "center" }: { framing: "wide" | "close" | "habitat"; focus: Vector3; calm: boolean; paused: boolean; interactive?: boolean; subject?: "egg" | "larva" | "pupa" | "adult"; composition?: "center" | "upper" }) {
  const controls = useRef<OrbitControlsImpl>(null);
  const camera = useThree(state => state.camera);
  const size = useThree(state => state.size);
  const aspect = size.width / size.height;
  const previousFocus = useRef(new Vector3()), delta = useRef(new Vector3());
  const interacting = useRef(false), initialized = useRef(false);
  useEffect(() => {
    const target = framing !== "wide" ? focus : wideTarget;
    const offset = framing !== "wide" ? new Vector3(10,9,20) : new Vector3(interactive ? 65 : 0, 22, 295);
    offset.multiplyScalar(Math.max(1, (framing === "wide" ? 0.35 : 0.8) / aspect));
    camera.position.copy(target).add(offset);
    if (camera instanceof PerspectiveCamera) {
      const fov = framing === "wide" ? 29 : framing === "habitat" ? 18 : { egg: 3.2, larva: 17, pupa: 13, adult: 12 }[subject];
      if (composition === "upper") camera.setViewOffset(size.width, size.height, 0, size.height * 0.20, size.width, size.height);
      else camera.clearViewOffset();
      camera.setFocalLength(0.5 * camera.getFilmHeight() / Math.tan(fov * Math.PI / 360));
    }
    controls.current?.target.copy(target); camera.lookAt(target); controls.current?.update();
    previousFocus.current.copy(focus); initialized.current = true;
  }, [camera, framing, focus, subject, aspect, interactive, composition, size.width, size.height]);
  useFrame((_, dt) => {
    if (!controls.current || !initialized.current) return;
    if (framing !== "wide" && !interacting.current) {
      delta.current.subVectors(focus, previousFocus.current);
      controls.current.target.add(delta.current); camera.position.add(delta.current);
    }
    previousFocus.current.copy(focus);
    const radial = Math.hypot(camera.position.x, camera.position.z);
    if (camera.position.y < 105 && radial < 13.5) {
      const factor = 13.5 / Math.max(radial, 0.001);
      camera.position.set(camera.position.x * factor, camera.position.y, camera.position.z * factor);
    }
    controls.current.autoRotate = interactive && !calm && !paused && !interacting.current && framing === "wide";
    controls.current.autoRotateSpeed = 0.09 * Math.min(dt * 60, 3);
  }, -1);
  return <OrbitControls ref={controls} makeDefault enabled={interactive} target={wideTarget} enablePan={false} enableDamping dampingFactor={0.08} minDistance={14} maxDistance={600} minPolarAngle={0.2} maxPolarAngle={Math.PI * 0.48} onStart={() => { interacting.current = true; }} onEnd={() => { interacting.current = false; }} />;
}
