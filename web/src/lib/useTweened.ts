import { animate, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";

/** A number that glides to its new value (for animated labels). */
export function useTweened(value: number, duration = 0.6): number {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(value);
  const current = useRef(value);
  useEffect(() => {
    if (reduce) {
      current.current = value;
      setShown(value);
      return;
    }
    const controls = animate(current.current, value, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => {
        current.current = v;
        setShown(v);
      },
    });
    return () => controls.stop();
  }, [value, duration, reduce]);
  return shown;
}
