/** Small seeded PRNG (mulberry32) so every run can be replayed. */
export type Rng = () => number;

export function makeRng(seed: number): Rng {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Draw an index with the given probabilities. */
export function drawIndex(probs: readonly number[], u: number): number {
  let acc = 0;
  for (let k = 0; k < probs.length; k++) {
    acc += probs[k];
    if (u < acc) return k;
  }
  return probs.length - 1;
}
