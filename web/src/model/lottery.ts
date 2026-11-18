/**
 * Layer 2: pairwise duels and the published maximal lottery (GT rule).
 */
import { CANDS, M, PERMS, RANK, countReports } from "./rankings";

export type Lottery = [number, number, number];

/** margins[a][b] = #reports with a above b  -  #reports with b above a. */
export function margins(reports: readonly number[]): number[][] {
  const counts = countReports(reports);
  const out = CANDS.map(() => CANDS.map(() => 0));
  PERMS.forEach((_, k) => {
    if (!counts[k]) return;
    for (const a of CANDS) {
      for (const b of CANDS) {
        if (a === b) continue;
        out[a][b] += RANK[k][a] < RANK[k][b] ? counts[k] : -counts[k];
      }
    }
  });
  return out;
}

/** Head-to-head tallies: wins[a][b] = #reports ranking a above b. */
export function duelTallies(reports: readonly number[]): number[][] {
  const out = CANDS.map(() => CANDS.map(() => 0));
  for (const k of reports) {
    for (const a of CANDS) {
      for (const b of CANDS) {
        if (a !== b && RANK[k][a] < RANK[k][b]) out[a][b] += 1;
      }
    }
  }
  return out;
}

/** Candidate that beats every rival (strict Condorcet winner), else null. */
export function condorcetWinner(mg: number[][]): number | null {
  for (const a of CANDS) {
    if (CANDS.every((b) => a === b || mg[a][b] > 0)) return a;
  }
  return null;
}

/** Candidate that loses to every rival (strict Condorcet loser), else null. */
export function condorcetLoser(mg: number[][]): number | null {
  for (const a of CANDS) {
    if (CANDS.every((b) => a === b || mg[a][b] < 0)) return a;
  }
  return null;
}

/**
 * Maximal lottery for three candidates.
 *
 * With complete strict rankings and an odd number of voters every off-diagonal
 * margin is a non-zero odd integer, so the lottery is unique: a strict
 * Condorcet winner gets probability one, and a three-cycle x -> y -> z -> x
 * gives each candidate the margin of the duel it is not part of,
 * p_x = m(y,z) / S, p_y = m(z,x) / S, p_z = m(x,y) / S.
 */
export function maximalLottery(mg: number[][]): Lottery {
  const w = condorcetWinner(mg);
  if (w !== null) {
    const p: Lottery = [0, 0, 0];
    p[w] = 1;
    return p;
  }
  if (CANDS.some((a) => CANDS.some((b) => a !== b && mg[a][b] === 0))) {
    // Only reachable with an even electorate; the app always uses odd n.
    throw new Error("maximalLottery: tied duel (use an odd number of voters)");
  }
  // Orient the cycle: either 0 -> 1 -> 2 -> 0 or 0 -> 2 -> 1 -> 0.
  const [x, y, z] = mg[0][1] > 0 ? [0, 1, 2] : [0, 2, 1];
  const mxy = mg[x][y];
  const myz = mg[y][z];
  const mzx = mg[z][x];
  const s = mxy + myz + mzx;
  const p: Lottery = [0, 0, 0];
  p[x] = myz / s;
  p[y] = mzx / s;
  p[z] = mxy / s;
  return p;
}

/** p - 1/m: positive for candidates above a fair share, negative below. */
export function centered(p: readonly number[]): number[] {
  return p.map((v) => v - 1 / M);
}
