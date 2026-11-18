/**
 * Layer 1: the voter's response to the published lottery.
 *
 * Degree/rank-normalized cubic score (gtiv ``score_formulation="degree_rank"``):
 *
 *   s_i(sigma) = mean_{j in N(i)} f( <p - 1/m, r_j - r_sigma> / (m - 1) ),  f(x) = x^3
 *
 * followed by the logit response q_i = softmax(beta * s_i).
 */
import { CANDS, M, N_PERMS, PERM_IDS, RANK } from "./rankings";

export const cube = (v: number) => v * v * v;

/**
 * How far card ``mine`` is "ahead" of a friend's card ``theirs``: for every
 * candidate, places gained relative to the friend, weighted by how hot the
 * candidate is on the scoreboard (p - 1/m). Lies in [-1, 1].
 */
export function contrast(pTilde: readonly number[], theirs: number, mine: number): number {
  let total = 0;
  for (const c of CANDS) total += pTilde[c] * (RANK[theirs][c] - RANK[mine][c]);
  return total / (M - 1);
}

/** Per-candidate pieces of ``contrast`` (they add up to it). */
export function contrastParts(pTilde: readonly number[], theirs: number, mine: number): number[] {
  return CANDS.map((c) => (pTilde[c] * (RANK[theirs][c] - RANK[mine][c])) / (M - 1));
}

/** Score of writing card ``mine`` given the friends' reports. Isolated voters score 0. */
export function cardScore(pTilde: readonly number[], friendReports: readonly number[], mine: number): number {
  if (friendReports.length === 0) return 0;
  let total = 0;
  for (const theirs of friendReports) total += cube(contrast(pTilde, theirs, mine));
  return total / friendReports.length;
}

export function allScores(pTilde: readonly number[], friendReports: readonly number[]): number[] {
  return PERM_IDS.map((k) => cardScore(pTilde, friendReports, k));
}

const TINY = Number.MIN_VALUE;

/** Stable, strictly positive softmax(beta * scores) (mirrors gtiv.core.utils.floored_softmax). */
export function softmax(scores: readonly number[], beta: number): number[] {
  const logits = scores.map((s) => beta * s);
  const top = Math.max(...logits);
  const w = logits.map((l) => Math.max(Math.exp(l - top), TINY));
  const z = w.reduce((a, b) => a + b, 0);
  return w.map((v) => v / z);
}

/** Fraction of the response mass that goes to the best-scoring cards. */
export function topMass(q: readonly number[], scores: readonly number[]): number {
  const best = Math.max(...scores);
  let mass = 0;
  for (let k = 0; k < N_PERMS; k++) if (scores[k] >= best - 1e-12) mass += q[k];
  return mass;
}
