import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Bloom, DepthOfField, EffectComposer, Noise, SSAO, Vignette } from "@react-three/postprocessing";
import { BlendFunction, DepthOfFieldEffect } from "postprocessing";
import { PerspectiveCamera, Vector3 } from "three";
import type { Quality } from "./types";

export function Post({ quality, focus }: { quality: Quality; focus: Vector3 }) {
  const dof = useRef<DepthOfFieldEffect>(null);
  useFrame(({ camera }) => {
    if (!dof.current || !(camera instanceof PerspectiveCamera)) return;
    dof.current.target?.copy(focus);
    // Thin-lens DOF approximation (1.1mm floor for readable inspection): f/5.6, 3 micrometre sensor circle of confusion.
    // All scene distances and the small sensor lens focal length are in mm.
    const distance = camera.position.distanceTo(focus), focal = camera.getFocalLength();
    dof.current.cocMaterial.worldFocusRange = Math.max(1.1, Math.min(24, 2 * 5.6 * 0.003 * distance * distance / (focal * focal)));
  });
  if (quality === "low") return null;
  return <EffectComposer multisampling={0} enableNormalPass={quality === "high"}>
    {quality === "high" ? <SSAO radius={1.2} intensity={0.65} luminanceInfluence={0.6} samples={8} rings={3} /> : <></>}
    <DepthOfField ref={dof} target={focus} worldFocusRange={1} bokehScale={quality === "high" ? 4 : 2.5} resolutionScale={0.5} />
    <Bloom intensity={0.08} luminanceThreshold={1.8} mipmapBlur />
    <Noise opacity={0.012} blendFunction={BlendFunction.SOFT_LIGHT} />
    <Vignette offset={0.32} darkness={0.3} />
  </EffectComposer>;
}
