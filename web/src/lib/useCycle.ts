import { useEffect, useState } from "react";

/** Counts 0, 1, 2, ... every ``ms`` milliseconds while ``on`` is true. */
export function useTicker(ms: number, on = true) {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!on) return;
    const id = window.setInterval(() => setTick((t) => t + 1), ms);
    return () => window.clearInterval(id);
  }, [ms, on]);
  return tick;
}
