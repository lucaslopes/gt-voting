import { useCallback, useEffect, useRef, useState } from "react";
import { createSim, resolveRound, stepMany, stepSim, type Network, type Sim } from "../model/simulation";
import type { Params } from "../model/update";

export type Speed = "slow" | "normal" | "fast" | "turbo";

export const SPEEDS: Record<Speed, { label: string; ms: number; perTick: number }> = {
  slow: { label: "Slow", ms: 900, perTick: 1 },
  normal: { label: "Normal", ms: 320, perTick: 1 },
  fast: { label: "Fast", ms: 80, perTick: 1 },
  turbo: { label: "Turbo", ms: 60, perTick: 60 },
};

/** Runs a classroom simulation on a timer. Parameter changes apply from the next round on. */
export function useSim({
  hearts,
  network,
  seed,
  params,
  running,
  speed,
}: {
  hearts: readonly number[];
  network: Network;
  seed: number;
  params: Params;
  running: boolean;
  speed: Speed;
}) {
  const [sim, setSim] = useState<Sim>(() => createSim(hearts, network, seed));
  const paramsRef = useRef(params);
  paramsRef.current = params;
  const heartsKey = hearts.join(",");

  useEffect(() => {
    setSim(createSim(hearts, network, seed));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [heartsKey, network, seed]);

  useEffect(() => {
    if (!running) return;
    const { ms, perTick } = SPEEDS[speed];
    const id = window.setInterval(() => setSim((s) => stepMany(s, paramsRef.current, perTick)), ms);
    return () => window.clearInterval(id);
  }, [running, speed]);

  const step = useCallback(() => setSim((s) => stepSim(s, paramsRef.current)), []);
  const reset = useCallback(() => setSim(createSim(hearts, network, seed)), [heartsKey, network, seed]); // eslint-disable-line react-hooks/exhaustive-deps
  /** Re-make the latest round's decisions with new dials (same ballots, same board). */
  const redecide = useCallback(
    (p: Params) =>
      setSim((s) => {
        if (!s.last) return s;
        const round = resolveRound(s.t, s.hearts, s.last.xBefore, s.last.reports, s.network, p);
        return { ...s, x: round.xAfter, last: round };
      }),
    [],
  );
  const jump = useCallback((rounds: number) => setSim((s) => stepMany(s, paramsRef.current, rounds)), []);
  return { sim, step, reset, jump, redecide };
}
