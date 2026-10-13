"use client";

import dynamic from "next/dynamic";
import { Component, useCallback, useImperativeHandle, useRef, type ReactNode, type Ref } from "react";
import { Fallback } from "./Fallback";
import type { VivariumHandle, VivariumProps } from "./types";

const Scene = dynamic(() => import("./Scene"), { ssr: false, loading: () => <Fallback loading message="飼育びんを準備しています" /> });
class RenderBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}
/** Import only this entry point; Three.js remains in an on-demand client chunk. */
export function Vivarium({ ref, className, ...props }: VivariumProps & { ref?: Ref<VivariumHandle> }) {
  const inner = useRef<VivariumHandle>(null);
  const pending = useRef<{ behaviour?: Parameters<VivariumHandle["setBehaviour"]>[0]; point?: Parameters<VivariumHandle["pointOfInterest"]>[0] }>({});
  useImperativeHandle(ref, () => ({
    setBehaviour(behaviour) { if (inner.current) inner.current.setBehaviour(behaviour); else pending.current.behaviour = behaviour; },
    pointOfInterest(point) { if (inner.current) inner.current.pointOfInterest(point); else pending.current.point = point; },
  }), []);
  const attachController = useCallback((controller: VivariumHandle | null) => {
    inner.current = controller;
    if (!controller) return;
    if (pending.current.behaviour) controller.setBehaviour(pending.current.behaviour);
    if (pending.current.point) controller.pointOfInterest(pending.current.point);
    pending.current = {};
  }, []);
  return <div className={className} style={{ position: "relative", width: "100%", height: "100%", minHeight: props.snapshot ? 0 : 280, isolation: "isolate" }} aria-label="ショウジョウバエの飼育びん" role="img">
    <RenderBoundary fallback={<Fallback stage={props.stage} />}>
      <Scene {...props} controllerRef={attachController} />
    </RenderBoundary>
  </div>;
}
export type { VivariumHandle, VivariumProps, Habitat, Stage, Behaviour, Quality, Phenotype } from "./types";
