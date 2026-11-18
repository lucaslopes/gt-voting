/**
 * One classroom of voters running the GTIV reporting loop.
 *
 * Round t (same timing as gtiv.core.voting_system.IterativeVotingSystem.step):
 *   1. every voter draws a report from their jar x_i^{t-1}
 *   2. the full profile is aggregated into the published maximal lottery p_t
 *   3. each voter scores all six cards against the friends' reports and p_t,
 *      turns scores into a response q_i = softmax(beta * s_i)
 *   4. jars update: x_i^t = (1-eta) x_i^{t-1} + eta[(1-alpha) q_i + alpha delta_heart]
 */
import { condorcetLoser, condorcetWinner, centered, margins, maximalLottery, type Lottery } from "./lottery";
import { delta, permIndex } from "./rankings";
import { allScores, softmax } from "./response";
import { makeRng, drawIndex } from "./rng";
import { nextJar, planMix, type Params } from "./update";

export type Network = "everyone" | "circle";

/** Friends a voter watches: everybody else, or the two nearest seats on each side. */
export function friendsOf(i: number, n: number, network: Network): number[] {
  if (network === "everyone") return Array.from({ length: n }, (_, j) => j).filter((j) => j !== i);
  const out = new Set<number>();
  for (const d of [-2, -1, 1, 2]) out.add((i + d + n) % n);
  out.delete(i);
  return [...out];
}

export interface Decision {
  voter: number;
  heart: number;
  friends: number[];
  friendReports: number[];
  report: number;
  p: Lottery;
  pTilde: number[];
  scores: number[];
  q: number[];
  plan: number[];
  xBefore: number[];
  xAfter: number[];
}

/** Everything one voter computes in a round, for any parameter choice. */
export function decide(
  voter: number,
  hearts: readonly number[],
  xBefore: readonly number[],
  reports: readonly number[],
  p: Lottery,
  network: Network,
  params: Params,
): Decision {
  const friends = friendsOf(voter, hearts.length, network);
  const friendReports = friends.map((j) => reports[j]);
  const pTilde = centered(p);
  const scores = allScores(pTilde, friendReports);
  const q = softmax(scores, params.beta);
  const plan = planMix(q, hearts[voter], params.alpha);
  const xAfter = nextJar(xBefore, plan, params.eta);
  return {
    voter,
    heart: hearts[voter],
    friends,
    friendReports,
    report: reports[voter],
    p,
    pTilde,
    scores,
    q,
    plan,
    xBefore: [...xBefore],
    xAfter,
  };
}

export interface Round {
  t: number;
  xBefore: number[][];
  reports: number[];
  margins: number[][];
  p: Lottery;
  winner: number | null;
  loser: number | null;
  params: Params;
  xAfter: number[][];
}

/** Aggregate a profile and update every jar. */
export function resolveRound(
  t: number,
  hearts: readonly number[],
  xBefore: number[][],
  reports: number[],
  network: Network,
  params: Params,
): Round {
  const mg = margins(reports);
  const p = maximalLottery(mg);
  const xAfter = hearts.map((_, i) => decide(i, hearts, xBefore[i], reports, p, network, params).xAfter);
  return {
    t,
    xBefore,
    reports,
    margins: mg,
    p,
    winner: condorcetWinner(mg),
    loser: condorcetLoser(mg),
    params: { ...params },
    xAfter,
  };
}

/** Reproducible per-round randomness: round t of seed s always draws the same numbers. */
export function roundRng(seed: number, t: number) {
  return makeRng((Math.imul(seed + 1, 0x9e3779b1) ^ Math.imul(t + 1, 0x85ebca6b)) >>> 0);
}

export function drawReports(x: readonly (readonly number[])[], seed: number, t: number): number[] {
  const rng = roundRng(seed, t);
  return x.map((jar) => drawIndex(jar, rng()));
}

export interface Stats {
  rounds: number;
  wins: number[];
  losses: number[];
  cycles: number;
  pSum: number[];
}

export interface Sim {
  hearts: number[];
  network: Network;
  seed: number;
  t: number;
  x: number[][];
  last: Round | null;
  /** Small summaries for the timeline (most recent last). */
  timeline: { t: number; p: Lottery; winner: number | null; loser: number | null }[];
  stats: Stats;
}

const TIMELINE = 240;

export function createSim(hearts: readonly number[], network: Network, seed: number): Sim {
  return {
    hearts: [...hearts],
    network,
    seed,
    t: 0,
    x: hearts.map((h) => delta(h)),
    last: null,
    timeline: [],
    stats: { rounds: 0, wins: [0, 0, 0], losses: [0, 0, 0], cycles: 0, pSum: [0, 0, 0] },
  };
}

export function stepSim(sim: Sim, params: Params): Sim {
  const t = sim.t + 1;
  const reports = drawReports(sim.x, sim.seed, t);
  const round = resolveRound(t, sim.hearts, sim.x, reports, sim.network, params);
  const stats: Stats = {
    rounds: sim.stats.rounds + 1,
    wins: [...sim.stats.wins],
    losses: [...sim.stats.losses],
    cycles: sim.stats.cycles + (round.winner === null ? 1 : 0),
    pSum: sim.stats.pSum.map((v, c) => v + round.p[c]),
  };
  if (round.winner !== null) stats.wins[round.winner] += 1;
  if (round.loser !== null) stats.losses[round.loser] += 1;
  const timeline = [...sim.timeline, { t, p: round.p, winner: round.winner, loser: round.loser }];
  if (timeline.length > TIMELINE) timeline.splice(0, timeline.length - TIMELINE);
  return { ...sim, t, x: round.xAfter, last: round, timeline, stats };
}

/** Run many rounds quickly (no per-round React state). */
export function stepMany(sim: Sim, params: Params, rounds: number): Sim {
  let s = sim;
  for (let r = 0; r < rounds; r++) s = stepSim(s, params);
  return s;
}

/** The story's example: 7 x ACB, 7 x BCA, 1 x ABC (A wins every duel 8-7). */
export function storyClass(): number[] {
  return [
    ...Array(7).fill(permIndex("ACB")),
    ...Array(7).fill(permIndex("BCA")),
    permIndex("ABC"),
  ];
}

/** Five of each cyclic ranking: a perfect rock-paper-scissors class. */
export function rockPaperScissorsClass(): number[] {
  const out: number[] = [];
  for (let r = 0; r < 5; r++) out.push(permIndex("ABC"), permIndex("BCA"), permIndex("CAB"));
  return out;
}

/** Random hearts (odd class size keeps every duel decisive). */
export function randomClass(n: number, seed: number): number[] {
  const rng = makeRng(seed ^ 0x5bd1e995);
  return Array.from({ length: n }, () => Math.floor(rng() * 6));
}
