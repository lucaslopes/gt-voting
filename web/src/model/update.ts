/**
 * The anchored update:
 *
 *   x_i^t = (1 - eta) x_i^{t-1} + eta [ (1 - alpha) q_i + alpha delta_{baseline_i} ]
 *
 * alpha = loyalty (pull back to the baseline ranking),
 * eta   = volatility (how much of the jar is replaced per round),
 * beta  = receptivity (enters through q_i = softmax(beta * score)).
 */
import { PERM_IDS } from "./rankings";

export interface Params {
  /** loyalty */
  alpha: number;
  /** volatility */
  eta: number;
  /** receptivity */
  beta: number;
}

/** The voter's plan: alpha parts heart ranking, (1 - alpha) parts response. */
export function planMix(q: readonly number[], heart: number, alpha: number): number[] {
  return PERM_IDS.map((k) => (1 - alpha) * q[k] + (k === heart ? alpha : 0));
}

/** The new jar: keep (1 - eta) of the old jar, refill eta from the plan. */
export function nextJar(x: readonly number[], plan: readonly number[], eta: number): number[] {
  return PERM_IDS.map((k) => (1 - eta) * x[k] + eta * plan[k]);
}
