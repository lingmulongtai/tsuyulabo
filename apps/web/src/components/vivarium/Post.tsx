import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Bloom, DepthOfField, EffectComposer, Noise, SSAO, Vignette } from "@react-three/postprocessing";
import { BlendFunction, DepthOfFieldEffect } from "postprocessing";
import { Vector3 } from "three";
import type { Quality } from "./types";

export function Post({ quality, focus }: { quality: Quality; focus: Vector3 }) {
  const dof = useRef<DepthOfFieldEffect>(null);
  useFrame(() => { dof.current?.target?.copy(focus); });
  if (quality === "low") return null;
  return <EffectComposer multisampling={quality === "high" ? 4 : 0} enableNormalPass={quality === "high"}>
    {quality === "high" ? <SSAO radius={0.08} intensity={1.1} luminanceInfluence={0.6} samples={8} rings={3} /> : <></>}
    <DepthOfField ref={dof} target={focus} worldFocusRange={0.27} bokehScale={quality === "high" ? 3 : 1.5} resolutionScale={0.5} />
    <Bloom intensity={0.12} luminanceThreshold={1.4} mipmapBlur />
    <Noise opacity={0.022} blendFunction={BlendFunction.SOFT_LIGHT} />
    <Vignette offset={0.28} darkness={0.38} />
  </EffectComposer>;
}
