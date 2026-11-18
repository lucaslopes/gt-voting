import { describe, expect, it } from "vitest";
import fixture from "./__fixtures__/parity.json";
import { margins, maximalLottery } from "./lottery";
import { permIndex } from "./rankings";
import { allScores, softmax } from "./response";
import { createSim, decide, storyClass, resolveRound, stepMany, type Network } from "./simulation";

const close = (a: number[], b: number[], tol = 1e-9) => {
  expect(a.length).toBe(b.length);
  a.forEach((v, i) => expect(Math.abs(v - b[i])).toBeLessThan(tol));
};

describe("maximal lottery", () => {
  it("gives a strict Condorcet winner everything (story baseline: A wins 8-7 twice)", () => {
    const mg = margins(storyClass());
    expect(mg[0][1]).toBe(1);
    expect(mg[0][2]).toBe(1);
    expect(mg[1][2]).toBe(1);
    expect(maximalLottery(mg)).toEqual([1, 0, 0]);
  });

  it("splits a cycle by the opposite margins (6/5/4 blocks -> 7/15, 3/15, 5/15)", () => {
    const reports = [
      ...Array(6).fill(permIndex("ABC")),
      ...Array(5).fill(permIndex("BCA")),
      ...Array(4).fill(permIndex("CAB")),
    ];
    close(maximalLottery(margins(reports)), [7 / 15, 3 / 15, 5 / 15], 1e-12);
  });

  it("one edited ballot (ABC -> CAB) makes C the winner", () => {
    const reports = storyClass();
    reports[14] = permIndex("CAB");
    expect(maximalLottery(margins(reports))).toEqual([0, 0, 1]);
  });
});

describe("response", () => {
  it("matches the hand computation for a BCA voter facing p = delta_A", () => {
    const reports = storyClass();
    const friends = reports.filter((_, j) => j !== 7); // voter 7 has heart BCA
    const s = allScores([2 / 3, -1 / 3, -1 / 3], friends);
    // A on top: 6 BCA friends are 2 places behind -> 6 * 1^3 / 14
    expect(s[permIndex("ABC")]).toBeCloseTo(6 / 14, 12);
    expect(s[permIndex("BAC")]).toBeCloseTo((6 * 0.125 - 8 * 0.125) / 14, 12);
    expect(s[permIndex("BCA")]).toBeCloseTo(-8 / 14, 12);
  });

  it("beta = 0 ignores the scoreboard", () => {
    softmax([0.4, -0.2, 0.1, 0, 0.9, -1], 0).forEach((v) => expect(v).toBeCloseTo(1 / 6, 12));
  });
});

describe("parity with the GTIV Rust assembly", () => {
  for (const c of fixture.cases) {
    it(`${c.name}: replays ${c.rounds.length} recorded rounds`, () => {
      const params = { alpha: c.alpha, eta: c.eta, beta: c.beta };
      c.rounds.forEach((r, t) => {
        const round = resolveRound(t + 1, c.hearts, r.xBefore, r.reports, c.network as Network, params);
        close(round.p, r.p, 1e-9);
        round.xAfter.forEach((row, i) => close(row, r.xAfter[i], 1e-9));
      });
    });
  }
});

describe("simulation", () => {
  it("is reproducible from the seed and keeps jars normalised", () => {
    const params = { alpha: 0.4, eta: 0.5, beta: 12 };
    const a = stepMany(createSim(storyClass(), "everyone", 7), params, 50);
    const b = stepMany(createSim(storyClass(), "everyone", 7), params, 50);
    expect(a.timeline.map((s) => s.winner)).toEqual(b.timeline.map((s) => s.winner));
    a.x.forEach((jar) => expect(jar.reduce((u, v) => u + v, 0)).toBeCloseTo(1, 12));
  });

  it("full loyalty freezes everyone at their heart ranking", () => {
    const sim = stepMany(createSim(storyClass(), "everyone", 1), { alpha: 1, eta: 0.6, beta: 30 }, 30);
    expect(sim.stats.wins).toEqual([30, 0, 0]);
  });

  it("decide() exposes the pipeline the story narrates", () => {
    const hearts = storyClass();
    const d = decide(7, hearts, [0, 0, 0, 1, 0, 0], hearts, [1, 0, 0], "everyone", {
      alpha: 0.5,
      eta: 0.5,
      beta: 10,
    });
    expect(d.friends).toHaveLength(14);
    close(d.plan, d.q.map((v, k) => 0.5 * v + (k === 3 ? 0.5 : 0)), 1e-12);
    close(d.xAfter, d.xBefore.map((v, k) => 0.5 * v + 0.5 * d.plan[k]), 1e-12);
  });
});
