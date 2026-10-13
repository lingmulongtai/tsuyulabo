"use client";
import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { useCareStage } from "./CareStage";
import { stageFraming } from "./framing";
import { useHome, useBehavior } from "@/lib/api/hooks";
import { decodedBehaviour, habitat, sitePosition, type VialState } from "@/game/vial";
import { Vivarium, type VivariumProps } from "./Vivarium";

export function CareVial({ vial, children, ...props }: VivariumProps & { vial?: VialState; children?: ReactNode }) {
  const slot = useCareStage();
  const register = slot?.register;
  useEffect(() => register?.(), [register]);
  const home = useHome();
  const current = home.data;
  const brain = useBehavior(current?.week?.id ?? "");
  const saved = vial ?? current?.vial;
  const surface = <div style={slot ? { position: "absolute", inset: 0 } : { height: "min(65dvh, 540px)", minHeight: 320 }} className={slot ? "overflow-hidden" : "relative overflow-hidden rounded-xl"} data-care-vial>
    <Vivarium stage={current?.fly?.stage ?? "egg"} seed={current?.week?.id} environment={habitat(saved)} pupationPosition={sitePosition(saved?.pupation_position)} framing={props.onGlassStroke || props.onGlassPick ? "wide" : stageFraming(props.stage ?? current?.fly?.stage ?? "egg")} composition={slot ? "upper" : "center"} {...props} paused={Boolean(slot?.paused || props.paused)} behaviour={props.behaviour ?? decodedBehaviour(brain.data)} />
    {children && <div className="pointer-events-none absolute inset-x-0 bottom-0 [&>*]:pointer-events-auto" style={{ top: slot ? "calc(96px + env(safe-area-inset-top))" : 0 }}>{children}</div>}
  </div>;
  return slot ? slot.host ? createPortal(surface, slot.host) : null : surface;
}
