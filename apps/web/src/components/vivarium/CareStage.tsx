"use client";
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { useIsMutating } from "@tanstack/react-query";
import { useAdults, useBehavior, useHome } from "@/lib/api/hooks";
import { decodedBehaviour, habitat, sitePosition } from "@/game/vial";
import { Vivarium } from "./Vivarium";
import { stageFraming } from "./framing";

const CareStageContext = createContext<{ host: HTMLDivElement | null; register: () => () => void; paused: boolean } | null>(null);
export const useCareStage = () => useContext(CareStageContext);

function CurrentScene({ paused }: { paused: boolean }) {
  const home = useHome(), data = home.data;
  const adults = useAdults();
  const adult = !data?.week ? data?.team.members[0] ?? adults.data?.[0] : undefined;
  const brain = useBehavior(data?.week?.id ?? adult?.id ?? "");
  const stage = adult ? "adult" : data?.fly?.stage ?? "egg";
  const vial = adult?.vial ?? data?.vial;
  return <div className="absolute inset-0" data-care-stage={stage}><Vivarium stage={stage} seed={data?.week?.id ?? adult?.id} sex={adult?.sex} traits={adult?.phenotypes} framing={stageFraming(stage)} composition="upper" paused={paused} environment={habitat(vial)} pupationPosition={sitePosition(vial?.pupation_position)} behaviour={decodedBehaviour(brain.data)} /></div>;
}

/** Only one scene is displayed: a game's live care surface replaces the default backdrop. */
export function CareStage({ children }: { children: ReactNode }) {
  const paused = useIsMutating() > 0;
  const [host, setHost] = useState<HTMLDivElement | null>(null);
  const [surfaces, setSurfaces] = useState(0);
  const register = useCallback(() => { setSurfaces(n => n + 1); return () => setSurfaces(n => n - 1); }, []);
  const value = useMemo(() => ({ host, register, paused }), [host, register, paused]);
  return <CareStageContext.Provider value={value}>
    <div className="fixed inset-0" aria-label="お世話中の飼育びん">
      {surfaces === 0 && <CurrentScene paused={paused} />}
      <div ref={setHost} className="absolute inset-0" />
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,.25),transparent_30%,rgba(0,0,0,.48))]" />
    </div>
    {children}
  </CareStageContext.Provider>;
}
