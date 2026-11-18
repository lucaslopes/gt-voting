export const pct = (v: number, digits = 0) => `${(v * 100).toFixed(digits)}%`;

/** Percent that never shows a misleading 0% or 100% for tiny but positive masses. */
export function pctSoft(v: number) {
  if (v <= 0) return "0%";
  if (v < 0.005) return "<1%";
  if (v > 0.995 && v < 1) return ">99%";
  return `${Math.round(v * 100)}%`;
}

export const signed = (v: number, digits = 2) => {
  const s = v.toFixed(digits);
  if (Number(s) === 0) return (0).toFixed(digits);
  return v > 0 ? `+${s}` : s.replace("-", "−");
};

export const fix = (v: number, digits = 2) => v.toFixed(digits);
