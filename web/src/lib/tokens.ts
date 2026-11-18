/** Turning probabilities into a whole number of cards in a jar. */
import { N_PERMS } from "../model/rankings";

export const JAR_CARDS = 20;

/** Largest-remainder rounding: integer counts that add up to ``total``. */
export function roundCounts(weights: readonly number[], total: number): number[] {
  const sum = weights.reduce((a, b) => a + b, 0) || 1;
  const raw = weights.map((w) => (w / sum) * total);
  const counts = raw.map(Math.floor);
  let left = total - counts.reduce((a, b) => a + b, 0);
  const order = raw.map((r, i) => [r - Math.floor(r), i] as const).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  for (const [, i] of order) {
    if (left <= 0) break;
    counts[i] += 1;
    left -= 1;
  }
  return counts;
}

export interface Token {
  id: string;
  k: number;
}

let serial = 0;
const fresh = (k: number): Token => ({ id: `t${serial++}`, k });

export function tokensFromCounts(counts: readonly number[]): Token[] {
  const out: Token[] = [];
  counts.forEach((n, k) => {
    for (let i = 0; i < n; i++) out.push(fresh(k));
  });
  return out;
}

export function jarTokens(x: readonly number[], total = JAR_CARDS): Token[] {
  return tokensFromCounts(roundCounts(x, total));
}

/**
 * Swap a share ``eta`` of the jar for cards drawn from ``plan``:
 * keeps round((1-eta) * total) old tokens (proportionally per card) and adds the rest from the plan.
 */
export function swapTokens(old: readonly Token[], plan: readonly number[], eta: number) {
  const total = old.length;
  const keepTotal = Math.round((1 - eta) * total);
  const oldCounts = new Array(N_PERMS).fill(0);
  old.forEach((t) => (oldCounts[t.k] += 1));
  const keepCounts = roundCounts(oldCounts, keepTotal);
  const inCounts = roundCounts(plan, total - keepTotal);
  const kept: Token[] = [];
  const left = [...keepCounts];
  for (const t of old) {
    if (left[t.k] > 0) {
      kept.push(t);
      left[t.k] -= 1;
    }
  }
  const incoming = tokensFromCounts(inCounts);
  return { tokens: [...kept, ...incoming], incoming: new Set(incoming.map((t) => t.id)) };
}
