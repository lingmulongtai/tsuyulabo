"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { ACESFilmicToneMapping, Group, SRGBColorSpace, Vector3 } from "three";
import { Adult } from "./Adult";
import { Egg } from "./Egg";
import { Larva } from "./Larva";
import { Pupa } from "./Pupa";
import { Vial } from "./Vial";
import { BenchEnvironment } from "./BenchEnvironment";
import { emergencePosition, toMillimetres, groundPosition, organismMM, radialMM, verticalMM } from "./scale";
import { Medium, foodHeight } from "./Medium";
import { Lighting } from "./Lighting";
import { CameraRig } from "./CameraRig";
import { Post } from "./Post";
import { Fallback } from "./Fallback";
import { GlassCare } from "./GlassCare";
import { FoodPour } from "./FoodPour";
import { BehaviourController } from "./controller";
import { carePose } from "./care-pose";
import { budgets, initialQuality, QualityMonitor } from "./quality";
import { useCalmMotion, usePageVisible } from "./lifecycle";
import { clamp01, displayStage, type Quality, type VivariumHandle, type VivariumProps } from "./types";

const wild = ["wild"] as const;
function World({ controller, focus, stage = "adult", environment = {}, sex = "f", traits = wild, seed = "tsuyu", paused, calm, selected, onTier, automatic, framing = "wide", composition, onSubjectPick, onGlassStroke, onGlassPick, wiped, pupationPosition = [0.24, -0.05, 0.94], pour, eclosionProgress }: VivariumProps & { controller: BehaviourController; focus: Vector3; calm: boolean; selected: Quality; automatic: boolean; onTier: (tier: Quality) => void }) {
  const organism = useRef<Group>(null);
  const monitor = useMemo(() => new QualityMonitor(), []);
  const metrics = useRef({ seconds: 0, frames: 0 });
  const kind = displayStage(stage);
  // Pose and shadow dirtiness must precede the transmission buffer capture.
  useFrame((state, dt) => {
    const thermalPace = Math.max(0.3, Math.min(1.5, ((environment.temperature ?? 25) - 12) / 13));
    const pose = paused ? controller.pose : controller.update(dt * thermalPace * clamp01(environment.pace, 1), stage, calm, !traits.includes("vestigial"));
    if (organism.current) {
      if (kind === "pupa") { organism.current.position.set(...toMillimetres(pupationPosition)); organism.current.rotation.set(0, 0, 0); }
      else if (stage === "wandering" || eclosionProgress !== undefined) {
        const care = carePose(pupationPosition, pose.phase, eclosionProgress);
        organism.current.position.set(...(eclosionProgress === undefined ? toMillimetres(care.position) : emergencePosition(pupationPosition, eclosionProgress))); organism.current.rotation.set(...care.rotation as [number, number, number]);
      }
      else { organism.current.position.set(...groundPosition(pose.position, kind)); organism.current.position.y += foodHeight(organism.current.position.x, organism.current.position.z) - 21.5; organism.current.rotation.y = pose.heading; }
      focus.set(organism.current.position.x, organism.current.position.y + ({ pupa: 0.2, adult: 0.045, larva: -0.035, egg: -0.052 }[kind]) * organismMM[kind], organism.current.position.z);
      if (kind === "adult") focus.set(focus.x + Math.sin(pose.heading) * 0.12 * organismMM.adult, focus.y, focus.z + Math.cos(pose.heading) * 0.12 * organismMM.adult);
    }
    if (!paused) {
      const tier = monitor.sample(dt, selected, automatic); if (tier !== selected) onTier(tier);
      metrics.current.seconds += dt; metrics.current.frames++;
      if (metrics.current.seconds >= 1) {
        const canvas = state.gl.domElement;
        canvas.dataset.fps = (metrics.current.frames / metrics.current.seconds).toFixed(1);
        canvas.dataset.drawCalls = String(state.gl.info.render.calls);
        canvas.dataset.triangles = String(state.gl.info.render.triangles);
        canvas.dataset.quality = selected;
        metrics.current = { seconds: 0, frames: 0 };
      }
    }
    state.gl.info.reset();
    // Share one shadow update between refraction, the main image and post passes.
    state.gl.shadowMap.needsUpdate = true;
    state.gl.domElement.dataset.ready = "true";
    state.gl.domElement.dataset.behaviour = controller.behaviour;
    state.gl.domElement.dataset.phase = controller.pose.phase.toFixed(3);
    state.gl.domElement.dataset.position = controller.pose.position.map(v => v.toFixed(3)).join(",");
  }, -2);
  return <>
    <color attach="background" args={["#59615a"]} />
    <fog attach="fog" args={["#59615a", 450, 1500]} />
    <BenchEnvironment />
    <Lighting quality={selected} />
    <Medium {...environment} />
    {pour && <group position={[0, 21.5 + 1.075 * verticalMM, 0]} scale={[radialMM, verticalMM, radialMM]}><FoodPour color={environment.food?.color} paused={Boolean(paused)} calm={calm} /></group>}
    <group ref={organism} onClick={event => { if (onSubjectPick && event.delta < 8) { event.stopPropagation(); onSubjectPick(); } }} scale={organismMM[kind]} position={kind === "pupa" ? toMillimetres(pupationPosition) : groundPosition(controller.pose.position, kind)}>
      {kind === "adult" ? <Adult pose={controller.pose} sex={sex} traits={traits} quality={selected} seed={seed} unfold={eclosionProgress === undefined ? 1 : clamp01((eclosionProgress - 0.25) / 0.65, 0)} /> : kind === "egg" ? <Egg /> : kind === "larva" ? <Larva pose={controller.pose} stage={stage} /> : <Pupa age={environment.pupaAge} />}
    </group>
    {eclosionProgress !== undefined && <group position={toMillimetres(pupationPosition)} scale={organismMM.pupa}><Pupa age={1} opened={Math.min(1, eclosionProgress * 4)} /></group>}
    <Vial humidity={environment.humidity} grime={environment.grime} quality={selected} wiped={wiped} />
    {(onGlassStroke || onGlassPick || wiped) && <GlassCare onGlassStroke={onGlassStroke} onGlassPick={onGlassPick} wiped={wiped} grime={environment.grime} mould={environment.mould} />}
    <CameraRig framing={framing} focus={focus} calm={calm} paused={Boolean(paused)} interactive={!onGlassStroke && !onGlassPick} subject={kind} composition={composition} />
    <Post quality={selected} focus={focus} />
  </>;
}

export default function Scene({ controllerRef, ...props }: VivariumProps & { controllerRef: (value: VivariumHandle | null) => void }) {
  const calm = useCalmMotion(), visible = usePageVisible();
  const [lost, setLost] = useState(false);
  const [tier, setTier] = useState<Quality>(() => initialQuality({ cores: navigator.hardwareConcurrency, memory: (navigator as Navigator & { deviceMemory?: number }).deviceMemory, mobile: matchMedia("(pointer: coarse)").matches }));
  const controller = useMemo(() => new BehaviourController(`${props.seed ?? "tsuyu"}:${props.stage ?? "adult"}`), [props.seed, props.stage]);
  const focus = useMemo(() => displayStage(props.stage ?? "adult") === "pupa" ? new Vector3(...toMillimetres([0.24, 0.15, 0.94])) : new Vector3(...groundPosition([0, -0.99, 0.12], displayStage(props.stage ?? "adult"))), [props.stage]);
  const selected = props.quality && props.quality !== "auto" ? props.quality : tier;
  const automatic = !props.quality || props.quality === "auto";
  const paused = props.paused || !visible;
  useEffect(() => { controller.setBehaviour(props.behaviour ?? "rest"); }, [controller, props.behaviour]);
  useEffect(() => { if (props.pointOfInterest) controller.pointOfInterest(props.pointOfInterest); }, [controller, props.pointOfInterest]);
  useEffect(() => { controllerRef(controller); return () => controllerRef(null); }, [controller, controllerRef]);
  const { onQualityChange } = props;
  useEffect(() => { onQualityChange?.(selected); }, [onQualityChange, selected]);
  const canvas = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    const element = canvas.current;
    const handleLost = (event: Event) => { event.preventDefault(); setLost(true); };
    element?.addEventListener("webglcontextlost", handleLost);
    return () => element?.removeEventListener("webglcontextlost", handleLost);
  }, []);
  if (lost) return <Fallback stage={props.stage} />;
  return <Canvas ref={canvas} shadows={budgets[selected].shadows} dpr={budgets[selected].dpr} frameloop={paused ? "demand" : "always"} camera={{ fov: 29, near: 0.1, far: 1600, filmGauge: 4.8, position: [65, 84, 295] }} gl={{ antialias: true, preserveDrawingBuffer: Boolean(props.snapshot), alpha: false, powerPreference: "high-performance", toneMapping: ACESFilmicToneMapping, outputColorSpace: SRGBColorSpace }} fallback={<Fallback stage={props.stage} />} onCreated={({ gl }) => {
    gl.toneMappingExposure = 1.1;
    gl.info.autoReset = false;
    gl.shadowMap.autoUpdate = false;
    const context = gl.getContext(), ext = context.getExtension("WEBGL_debug_renderer_info");
    if (automatic && ext) {
      const renderer = String(context.getParameter(ext.UNMASKED_RENDERER_WEBGL));
      if (/swiftshader|llvmpipe|software/i.test(renderer)) setTier("low");
    }
  }}>
    <Suspense fallback={null}><World {...props} controller={controller} focus={focus} calm={calm} paused={paused} selected={selected} automatic={automatic} onTier={setTier} /></Suspense>
  </Canvas>;
}
