import type { Stage } from "./types";

/** Close inspection of early stages; adults retain a little more habitat around them. */
export const stageFraming = (stage: Stage): "close" | "habitat" => stage === "adult" ? "habitat" : "close";
