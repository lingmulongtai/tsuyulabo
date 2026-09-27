"use client";

import { useMemo } from "react";
import { useBehavior } from "@/lib/api/hooks";
import { behaviorProbabilities } from "@/lib/api/behavior-display";
import { BehaviorFly } from "../art/BehaviorFly";
import type { Sex, Strain } from "../art/palette";
import { ErrorCard, QueryState } from "../ui/QueryState";

export function AdultBehavior({ id, strain, sex }: { id: string; strain: Strain; sex: Sex }) {
  const behavior = useBehavior(id);
  const mapped = useMemo(() => {
    try { return { probs: behavior.data ? behaviorProbabilities(behavior.data) : null, error: null }; }
    catch (error) { return { probs: null, error }; }
  }, [behavior.data]);
  if (mapped.error) return <ErrorCard error={mapped.error} retry={() => void behavior.refetch()} />;
  return <QueryState query={behavior}>{() => mapped.probs && <BehaviorFly key={id} probs={mapped.probs} strain={strain} sex={sex} />}</QueryState>;
}
