/** The story's fixed round (round 1 of the story's class) and the shared story dials. */
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { MIA, MIA_HEART, STORY_HEARTS, STORY_PARAMS, type ParamKey } from "../cast";
import { duelTallies, margins, maximalLottery } from "../model/lottery";
import { delta } from "../model/rankings";
import { decide } from "../model/simulation";
import type { Params } from "../model/update";

/** Round 1: every jar is full of heart cards, so every ballot is honest. */
export const R1_REPORTS = [...STORY_HEARTS];
export const R1_MARGINS = margins(R1_REPORTS);
export const R1_TALLIES = duelTallies(R1_REPORTS);
export const R1_P = maximalLottery(R1_MARGINS);

export function miaDecision(params: Params) {
  return decide(MIA, STORY_HEARTS, delta(MIA_HEART), R1_REPORTS, R1_P, "everyone", params);
}

interface StoryState {
  params: Params;
  set: (k: ParamKey, v: number) => void;
}

const Ctx = createContext<StoryState | null>(null);

export function StoryProvider({ children }: { children: ReactNode }) {
  const [params, setParams] = useState<Params>(STORY_PARAMS);
  const value = useMemo(
    () => ({ params, set: (k: ParamKey, v: number) => setParams((p) => ({ ...p, [k]: v })) }),
    [params],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useStory() {
  const s = useContext(Ctx);
  if (!s) throw new Error("useStory outside StoryProvider");
  return s;
}
