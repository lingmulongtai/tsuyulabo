"use client";
import type { ReactNode } from "react";
import { useHome, useBehavior } from "@/lib/api/hooks";
import { decodedBehaviour, habitat, sitePosition, type VialState } from "@/game/vial";
import { Vivarium, type VivariumProps } from "./Vivarium";

export function CareVial({ vial, children, ...props }: VivariumProps & { vial?: VialState; children?: ReactNode }) {
  const home = useHome();
  const current = home.data;
  const brain = useBehavior(current?.week?.id ?? "");
  const saved = vial ?? current?.vial;
  return <div style={{ height: "min(65dvh, 540px)", minHeight: 320 }} className="relative overflow-hidden rounded-xl" data-care-vial>
    <Vivarium stage={current?.fly?.stage ?? "egg"} seed={current?.week?.id} environment={habitat(saved)} pupationPosition={sitePosition(saved?.pupation_position)} {...props} behaviour={props.behaviour ?? decodedBehaviour(brain.data)} />
    {children}
  </div>;
}
