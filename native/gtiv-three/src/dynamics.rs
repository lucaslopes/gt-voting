//! GTIV iterative-voting dynamics: recurring assemblies that publish the
//! maximal lottery and let voters adapt their reporting tendencies.
//!
//! Every voter `i` has a sincere ranking
//! `R0_i` and a reporting tendency `x_i`, a probability vector over the `m!`
//! rankings. Each round:
//!
//! 1. every voter independently draws a report `R_i` from `x_i`;
//! 2. the rule publishes the maximal lottery `p = G(R)` (exact rational
//!    solver of [`crate::aggregate_rankings_with`]);
//! 3. every voter scores every ranking `sigma`,
//!    `s_i(sigma) = (1/d_i) sum_{j in N(i)} ( <p - (1/m) 1, rho(R_j) - rho(sigma)> / (m-1) )^3`,
//!    where `rho(sigma)[c]` is the position of candidate `c` in `sigma`
//!    (0 = top). This is a cubic score normalized by candidate positions
//!    and by the voter's number of neighbors;
//! 4. logit response `q_i(sigma) ∝ exp(beta_i s_i(sigma))` and update
//!    `x_i <- (1-eta_i) x_i + eta_i [ (1-alpha_i) q_i + alpha_i delta_{R0_i} ]`.
//!
//! The display (`p`) and the neighbours (`R_j`) are the two information
//! channels; each is [`Channel::Live`] (current value) or [`Channel::Fixed`]
//! (baseline value `p0 = G(R0)` or `R0_j`), giving the four arms.
//!
//! The assembly exposes this specific update rule to Rust callers. For
//! reproducible comparisons, use the same reports or replay the same
//! uniforms, explicitly select the lottery rule, and allow for rounding in
//! the floating-point update.
//!
//! Cost: one round is `O(u * m! * m + sum_i d_i * m!)` floating operations
//! and `O(n * m!)` memory, where `u <= min(n, m!)` is the number of distinct
//! scored reports. `m! = 40320` at `m = MAX_CANDIDATES = 8`, so large `m`
//! is expensive; `m = 2` and `m = 3` are cheap.
//!
//! Randomness is supplied by the caller through [`UniformSource`]; the
//! library never reads clocks, spawns threads or performs I/O. Last-bit
//! differences between native and Wasm builds can arise from the platform
//! `exp`.

use crate::general::{aggregate_rankings_with, GeneralOutcome, Selector, MAX_CANDIDATES};

/// `numpy.finfo(float64).tiny`, the floor of [`logit_response`].
pub const SOFTMAX_FLOOR: f64 = f64::MIN_POSITIVE;

/// A deterministic stream of uniform draws in `[0, 1)`, supplied by the
/// caller. [`Assembly::step`] consumes exactly one draw per voter per round,
/// in voter order `0..n`, and maps it to a ranking by inverse CDF exactly as
/// `numpy.random.Generator.choice(k, p=x_i)` does. Replaying numpy's
/// `Generator.random()` stream therefore reproduces GTIV's sampled reports.
pub trait UniformSource {
    fn next_uniform(&mut self) -> f64;
}

/// SplitMix64 (Steele, Lea and Flood 2014): a small seeded generator for
/// callers without their own. Output is `(z >> 11) * 2^-53`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }
    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
}

impl UniformSource for SplitMix64 {
    fn next_uniform(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
    }
}

/// Replays a recorded sequence of uniforms (e.g. numpy's `random()` stream).
/// Panics when exhausted.
#[derive(Debug, Clone)]
pub struct ReplayUniforms {
    values: Vec<f64>,
    next: usize,
}

impl ReplayUniforms {
    pub fn new(values: Vec<f64>) -> Self {
        Self { values, next: 0 }
    }
    pub fn consumed(&self) -> usize {
        self.next
    }
}

impl UniformSource for ReplayUniforms {
    fn next_uniform(&mut self) -> f64 {
        let u = self.values[self.next];
        self.next += 1;
        u
    }
}

/// All complete rankings of `m` candidates in lexicographic order, the order
/// of Python's `itertools.permutations(range(m))`. Ranking `k` lists
/// candidates from top to bottom; its rank vector `rho` gives each
/// candidate's position.
#[derive(Debug, Clone, PartialEq)]
pub struct RankingSpace {
    m: usize,
    rankings: Vec<Vec<usize>>,
    rank_vectors: Vec<Vec<f64>>,
}

impl RankingSpace {
    pub fn new(m: usize) -> Result<Self, &'static str> {
        if !(2..=MAX_CANDIDATES).contains(&m) {
            return Err("dynamics need between 2 and MAX_CANDIDATES candidates");
        }
        let mut rankings = Vec::new();
        let mut current: Vec<usize> = (0..m).collect();
        loop {
            rankings.push(current.clone());
            // Next lexicographic permutation.
            let Some(i) = (0..m - 1).rev().find(|&i| current[i] < current[i + 1]) else {
                break;
            };
            let j = (i + 1..m).rev().find(|&j| current[j] > current[i]).unwrap();
            current.swap(i, j);
            current[i + 1..].reverse();
        }
        let rank_vectors = rankings
            .iter()
            .map(|r| {
                let mut rho = vec![0.0; m];
                for (pos, &c) in r.iter().enumerate() {
                    rho[c] = pos as f64;
                }
                rho
            })
            .collect();
        Ok(Self {
            m,
            rankings,
            rank_vectors,
        })
    }
    pub fn candidates(&self) -> usize {
        self.m
    }
    /// `m!`.
    pub fn len(&self) -> usize {
        self.rankings.len()
    }
    pub fn is_empty(&self) -> bool {
        self.rankings.is_empty()
    }
    pub fn ranking(&self, k: usize) -> &[usize] {
        &self.rankings[k]
    }
    pub fn rank_vector(&self, k: usize) -> &[f64] {
        &self.rank_vectors[k]
    }
    /// Lexicographic index of a complete ranking (Lehmer code).
    pub fn index_of(&self, ranking: &[usize]) -> Option<usize> {
        if ranking.len() != self.m {
            return None;
        }
        let mut seen = vec![false; self.m];
        let mut index = 0usize;
        for (pos, &c) in ranking.iter().enumerate() {
            if c >= self.m || seen[c] {
                return None;
            }
            let smaller_unused = (0..c).filter(|&d| !seen[d]).count();
            index = index * (self.m - pos) + smaller_unused;
            seen[c] = true;
        }
        Some(index)
    }
}

/// Per-voter behavioural parameters; may change between rounds
/// ([`Assembly::set_params`]).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct VoterParams {
    /// Loyalty `alpha` in `[0, 1]`: weight on the sincere ranking.
    pub loyalty: f64,
    /// Receptivity `beta >= 0`, finite: logit sharpness (`0` = uniform noise).
    pub receptivity: f64,
    /// Volatility `eta` in `(0, 1]`: share of the tendency replaced per round.
    pub volatility: f64,
}

impl VoterParams {
    pub fn new(loyalty: f64, receptivity: f64, volatility: f64) -> Result<Self, &'static str> {
        let p = Self {
            loyalty,
            receptivity,
            volatility,
        };
        p.validate()?;
        Ok(p)
    }
    pub fn validate(&self) -> Result<(), &'static str> {
        if !(0.0..=1.0).contains(&self.loyalty) {
            return Err("loyalty alpha must lie in [0, 1]");
        }
        if !(self.receptivity.is_finite() && self.receptivity >= 0.0) {
            return Err("receptivity beta must be finite and non-negative");
        }
        if !(self.volatility > 0.0 && self.volatility <= 1.0) {
            return Err("volatility eta must lie in (0, 1]");
        }
        Ok(())
    }
}

/// Whether an information channel supplies its current or its baseline value.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Channel {
    Live,
    Fixed,
}

/// The two information channels; `Arms::FEEDBACK` (both live) is the
/// standard model.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Arms {
    /// The published lottery: live `p_t` or fixed `p0 = G(R0)`.
    pub display: Channel,
    /// The neighbours' reports: live `R_t` or fixed `R0`.
    pub neighbours: Channel,
}

impl Arms {
    pub const FEEDBACK: Arms = Arms {
        display: Channel::Live,
        neighbours: Channel::Live,
    };
    pub const BOTH_FIXED: Arms = Arms {
        display: Channel::Fixed,
        neighbours: Channel::Fixed,
    };
}

/// What one round produced.
#[derive(Debug, Clone, PartialEq)]
pub struct Round {
    /// Index of the round (0 for the first round stepped).
    pub index: u64,
    /// Report (ranking index) of every voter.
    pub reports: Vec<usize>,
    /// The published maximal lottery of `reports`, with exact certificate.
    pub published: GeneralOutcome,
    /// The lottery the voters scored against (`published` or `p0`).
    pub display: Vec<f64>,
}

/// Cube of the scaled contrast, `( <p~, rho_j - rho_sigma> / (m-1) )^3`, for
/// one neighbour report `j` against every ranking, in Python's operation order.
fn contrast_cubes(space: &RankingSpace, centered: &[f64], report: usize) -> Vec<f64> {
    let m = space.m;
    let rank_range = (m - 1).max(1) as f64;
    let rho_j = &space.rank_vectors[report];
    space
        .rank_vectors
        .iter()
        .map(|rho_k| {
            let mut contrast = 0.0;
            for c in 0..m {
                contrast += centered[c] * (rho_j[c] - rho_k[c]);
            }
            contrast /= rank_range;
            contrast * contrast * contrast
        })
        .collect()
}

/// Scores `s_i(sigma)` of every voter for every ranking, given the displayed
/// lottery and the neighbour reports each voter sees. A voter without
/// neighbours scores every ranking 0 (uniform response), as in GTIV.
pub fn scores(
    space: &RankingSpace,
    display: &[f64],
    neighbour_reports: &[usize],
    neighbours: &[Vec<usize>],
) -> Vec<Vec<f64>> {
    let k = space.len();
    let inv_m = 1.0 / space.m as f64;
    let centered: Vec<f64> = display.iter().map(|&p| p - inv_m).collect();
    let mut cache: Vec<Option<Vec<f64>>> = vec![None; k];
    for list in neighbours {
        for &j in list {
            let r = neighbour_reports[j];
            if cache[r].is_none() {
                cache[r] = Some(contrast_cubes(space, &centered, r));
            }
        }
    }
    neighbours
        .iter()
        .map(|list| {
            let mut total = vec![0.0; k];
            if list.is_empty() {
                return total;
            }
            for &j in list {
                let cubes = cache[neighbour_reports[j]].as_ref().unwrap();
                for (t, &c) in total.iter_mut().zip(cubes) {
                    *t += c;
                }
            }
            let degree = list.len() as f64;
            for t in &mut total {
                *t /= degree;
            }
            total
        })
        .collect()
}

/// Logit response `q(sigma) ∝ exp(beta s(sigma))` with GTIV's floored
/// softmax: shift by the maximum, clip logits to `[ln(tiny), 0]`, normalize,
/// floor at `tiny` and normalize again, so every entry is strictly positive.
pub fn logit_response(scores: &[f64], receptivity: f64) -> Vec<f64> {
    let max = scores.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    let log_floor = SOFTMAX_FLOOR.ln();
    let weights: Vec<f64> = scores
        .iter()
        .map(|&s| (receptivity * (s - max)).clamp(log_floor, 0.0).exp())
        .collect();
    let sum: f64 = weights.iter().sum();
    let floored: Vec<f64> = weights
        .iter()
        .map(|&w| (w / sum).max(SOFTMAX_FLOOR))
        .collect();
    let sum: f64 = floored.iter().sum();
    floored.iter().map(|&q| q / sum).collect()
}

/// `x <- (1-eta) x + eta [ (1-alpha) q + alpha delta_{sincere} ]`, in place.
pub fn update_tendency(
    tendency: &mut [f64],
    response: &[f64],
    sincere: usize,
    params: &VoterParams,
) {
    let (alpha, eta) = (params.loyalty, params.volatility);
    for (k, (x, &q)) in tendency.iter_mut().zip(response).enumerate() {
        let anchor = if k == sincere { 1.0 } else { 0.0 };
        *x = (1.0 - eta) * *x + eta * ((1.0 - alpha) * q + alpha * anchor);
    }
}

/// Draw a ranking index from `tendency` with one uniform, as numpy's
/// `Generator.choice(k, p=tendency)`: `cdf = cumsum(p) / cdf[-1]`, then the
/// first index whose `cdf` exceeds `u`.
pub fn draw_ranking(tendency: &[f64], u: f64) -> usize {
    let mut cdf = Vec::with_capacity(tendency.len());
    let mut acc = 0.0;
    for &x in tendency {
        acc += x;
        cdf.push(acc);
    }
    let last = acc;
    for c in &mut cdf {
        *c /= last;
    }
    cdf.partition_point(|&c| c <= u).min(tendency.len() - 1)
}

/// A recurring assembly of `n` voters over `m` candidates.
#[derive(Debug, Clone)]
pub struct Assembly {
    space: RankingSpace,
    sincere: Vec<usize>,
    params: Vec<VoterParams>,
    neighbours: Vec<Vec<usize>>,
    arms: Arms,
    tendencies: Vec<Vec<f64>>,
    baseline_lottery: GeneralOutcome,
    rounds: u64,
    selector: Selector,
}

/// Neighbourhoods of the clique on `n` voters (every voter sees all others).
pub fn clique(n: usize) -> Vec<Vec<usize>> {
    (0..n)
        .map(|i| (0..n).filter(|&j| j != i).collect())
        .collect()
}

impl Assembly {
    /// `sincere[i]` is voter `i`'s sincere ranking index in
    /// [`RankingSpace::new`] order; `neighbours[i]` lists whom voter `i`
    /// sees (no self-loops, no duplicates; sorted ascending internally, which
    /// fixes the summation order). Tendencies start at `delta_{R0_i}`.
    pub fn new(
        m: usize,
        sincere: Vec<usize>,
        params: Vec<VoterParams>,
        neighbours: Vec<Vec<usize>>,
        arms: Arms,
    ) -> Result<Self, &'static str> {
        let space = RankingSpace::new(m)?;
        let n = sincere.len();
        if n == 0 {
            return Err("an assembly needs at least one voter");
        }
        if params.len() != n || neighbours.len() != n {
            return Err("params and neighbours need one entry per voter");
        }
        if sincere.iter().any(|&k| k >= space.len()) {
            return Err("sincere ranking index out of range");
        }
        for p in &params {
            p.validate()?;
        }
        let mut sorted = neighbours;
        for (i, list) in sorted.iter_mut().enumerate() {
            list.sort_unstable();
            if list.windows(2).any(|w| w[0] == w[1]) {
                return Err("duplicate neighbour");
            }
            if list.iter().any(|&j| j >= n || j == i) {
                return Err("neighbour out of range or self-loop");
            }
        }
        let ballots: Vec<Vec<usize>> = sincere.iter().map(|&k| space.rankings[k].clone()).collect();
        let baseline_lottery = aggregate_rankings_with(&ballots, m, Selector::Vertex)?;
        let tendencies = sincere
            .iter()
            .map(|&k| {
                let mut x = vec![0.0; space.len()];
                x[k] = 1.0;
                x
            })
            .collect();
        Ok(Self {
            space,
            sincere,
            params,
            neighbours: sorted,
            arms,
            tendencies,
            baseline_lottery,
            rounds: 0,
            selector: Selector::Vertex,
        })
    }

    /// The selector of the published (and baseline) lottery on a
    /// non-unique GT face. [`Selector::Vertex`] (the default) is the
    /// behaviour of [`Assembly::new`]; [`Selector::MinimumNorm`] is GTIV's
    /// `gt_solver="qp-balanced"`, computed exactly.
    pub fn selector(&self) -> Selector {
        self.selector
    }

    /// Change the selector; the baseline lottery `p0 = G(R0)` is recomputed
    /// with it. Takes effect from the next round.
    pub fn set_selector(&mut self, selector: Selector) -> Result<(), &'static str> {
        self.selector = selector;
        self.baseline_lottery = self.lottery_of(&self.sincere.clone())?;
        Ok(())
    }

    fn lottery_of(&self, reports: &[usize]) -> Result<GeneralOutcome, &'static str> {
        let ballots: Vec<Vec<usize>> = reports
            .iter()
            .map(|&k| self.space.rankings[k].clone())
            .collect();
        aggregate_rankings_with(&ballots, self.space.m, self.selector)
    }

    /// Replace every voter's sincere ranking `R0` (ranking indices), for
    /// example after experience revised the voters' beliefs. Tendencies are
    /// kept; loyalty `alpha` anchors the new `R0` from the next round, and
    /// the baseline lottery `p0 = G(R0)` is recomputed. This revision is
    /// outside the GTIV model, whose `R0` is fixed.
    pub fn set_sincere(&mut self, sincere: Vec<usize>) -> Result<(), &'static str> {
        if sincere.len() != self.voters() {
            return Err("one sincere ranking per voter is required");
        }
        if sincere.iter().any(|&k| k >= self.space.len()) {
            return Err("sincere ranking index out of range");
        }
        let baseline = self.lottery_of(&sincere)?;
        self.sincere = sincere;
        self.baseline_lottery = baseline;
        Ok(())
    }

    pub fn space(&self) -> &RankingSpace {
        &self.space
    }
    pub fn voters(&self) -> usize {
        self.sincere.len()
    }
    pub fn sincere(&self) -> &[usize] {
        &self.sincere
    }
    pub fn neighbours(&self) -> &[Vec<usize>] {
        &self.neighbours
    }
    pub fn arms(&self) -> Arms {
        self.arms
    }
    pub fn set_arms(&mut self, arms: Arms) {
        self.arms = arms;
    }
    /// The one-shot lottery `p0 = G(R0)` of the sincere profile.
    pub fn baseline_lottery(&self) -> &GeneralOutcome {
        &self.baseline_lottery
    }
    pub fn rounds(&self) -> u64 {
        self.rounds
    }
    pub fn params(&self) -> &[VoterParams] {
        &self.params
    }
    /// Change voter `i`'s parameters; takes effect from the next round.
    pub fn set_params(&mut self, i: usize, params: VoterParams) -> Result<(), &'static str> {
        params.validate()?;
        *self.params.get_mut(i).ok_or("voter out of range")? = params;
        Ok(())
    }
    pub fn tendency(&self, i: usize) -> &[f64] {
        &self.tendencies[i]
    }
    pub fn tendencies(&self) -> &[Vec<f64>] {
        &self.tendencies
    }
    /// Replace voter `i`'s tendency (non-negative, sums to 1 within 1e-9).
    pub fn set_tendency(&mut self, i: usize, tendency: Vec<f64>) -> Result<(), &'static str> {
        if tendency.len() != self.space.len() {
            return Err("tendency needs one entry per ranking");
        }
        if tendency.iter().any(|&x| !(x >= 0.0 && x.is_finite())) {
            return Err("tendency entries must be finite and non-negative");
        }
        if (tendency.iter().sum::<f64>() - 1.0).abs() > 1e-9 {
            return Err("tendency must sum to 1");
        }
        *self.tendencies.get_mut(i).ok_or("voter out of range")? = tendency;
        Ok(())
    }

    /// Draw every voter's report from its tendency, one uniform per voter.
    pub fn draw_reports(&self, rng: &mut impl UniformSource) -> Vec<usize> {
        self.tendencies
            .iter()
            .map(|x| draw_ranking(x, rng.next_uniform()))
            .collect()
    }

    /// One full round: draw reports, then [`Assembly::step_with_reports`].
    pub fn step(&mut self, rng: &mut impl UniformSource) -> Result<Round, &'static str> {
        let reports = self.draw_reports(rng);
        self.step_with_reports(&reports)
    }

    /// Steps 2-4 of a round given the reports (ranking indices): publish the
    /// maximal lottery, score against the selected channels, respond and
    /// update every tendency.
    pub fn step_with_reports(&mut self, reports: &[usize]) -> Result<Round, &'static str> {
        let n = self.voters();
        if reports.len() != n || reports.iter().any(|&k| k >= self.space.len()) {
            return Err("one valid ranking index per voter is required");
        }
        let published = self.lottery_of(reports)?;
        let display = match self.arms.display {
            Channel::Live => published.probabilities.clone(),
            Channel::Fixed => self.baseline_lottery.probabilities.clone(),
        };
        let seen = match self.arms.neighbours {
            Channel::Live => reports,
            Channel::Fixed => &self.sincere[..],
        };
        let s = scores(&self.space, &display, seen, &self.neighbours);
        for i in 0..n {
            let q = logit_response(&s[i], self.params[i].receptivity);
            update_tendency(
                &mut self.tendencies[i],
                &q,
                self.sincere[i],
                &self.params[i],
            );
        }
        let round = Round {
            index: self.rounds,
            reports: reports.to_vec(),
            published,
            display,
        };
        self.rounds += 1;
        Ok(round)
    }
}
