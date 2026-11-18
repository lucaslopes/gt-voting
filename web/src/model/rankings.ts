/**
 * Rankings of three candidates.
 *
 * Index order matches Python's ``itertools.permutations(range(3))`` so that
 * baseline indices, fixtures and the gtiv package line up one to one.
 */

export const M = 3;
export type Cand = 0 | 1 | 2;
export const CANDS: readonly Cand[] = [0, 1, 2];

/** PERMS[k] lists candidates from top (1st) to bottom (3rd). */
export const PERMS: readonly (readonly [Cand, Cand, Cand])[] = [
  [0, 1, 2], // ABC
  [0, 2, 1], // ACB
  [1, 0, 2], // BAC
  [1, 2, 0], // BCA
  [2, 0, 1], // CAB
  [2, 1, 0], // CBA
];
export const N_PERMS = PERMS.length;
export const PERM_IDS = PERMS.map((_, k) => k);

/** RANK[k][c] = position of candidate c in ranking k (0 = top). */
export const RANK: readonly (readonly number[])[] = PERMS.map((perm) => {
  const r = [0, 0, 0];
  perm.forEach((c, pos) => {
    r[c] = pos;
  });
  return r;
});

const LETTERS = "ABC";

export function permLabel(k: number): string {
  return PERMS[k].map((c) => LETTERS[c]).join("");
}

export function permIndex(label: string): number {
  const k = PERMS.findIndex((_, i) => permLabel(i) === label.toUpperCase());
  if (k < 0) throw new Error(`unknown ranking ${label}`);
  return k;
}

/** Point mass on ranking k (a jar full of one card). */
export function delta(k: number): number[] {
  return PERM_IDS.map((j) => (j === k ? 1 : 0));
}

/** Number of reports (ballots) of each ranking. */
export function countReports(reports: readonly number[]): number[] {
  const counts = new Array(N_PERMS).fill(0);
  for (const k of reports) counts[k] += 1;
  return counts;
}
