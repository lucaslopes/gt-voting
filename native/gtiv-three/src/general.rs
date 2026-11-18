//! Exact GT lotteries for complete rankings of `1..=MAX_CANDIDATES` candidates.
//!
//! This extends the three-candidate adapter without changing it. The margin
//! convention follows the Python `GT` mechanism
//! (`M[i][j] = #(i over j) - #(j over i)`). Because `M` is skew-symmetric the
//! GT game value is zero, so the GT optimal-strategy face is
//! `{p : p >= 0, sum(p) = 1, M^T p >= 0}`. This module solves that face with an
//! exact rational two-phase simplex (Bland's rule), so it needs no LP crate.
//!
//! The default selector is deterministic: the first weak Condorcet winner in
//! candidate-ID order receives all mass (the same rule as [`crate::solve_three`]);
//! otherwise the vertex reached by phase one of the exact simplex is returned.
//! The Python LP solver may return a different vertex on a non-unique face.
//! [`FaceCertificate`] certifies uniqueness exactly by minimizing and maximizing
//! every coordinate over the face.
//!
//! [`Selector::MinimumNorm`] (`aggregate_rankings_with`, `solve_margins_with`)
//! instead computes the face's minimum-norm point exactly. It is equivariant
//! under relabelling the candidates.
//!
//! This ranking interface accepts complete, unweighted ballots. A caller with
//! a precomputed skew-symmetric margin matrix can use [`solve_margins`].

use std::cmp::Ordering;

/// Largest supported candidate count. Exact `i128` arithmetic is checked;
/// overflow is reported as an error rather than rounded.
pub const MAX_CANDIDATES: usize = 8;

/// Reduced rational number with a positive denominator.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Ratio {
    pub num: i128,
    pub den: i128,
}

const OVERFLOW: &str = "exact arithmetic overflow";

fn gcd(a: i128, b: i128) -> u128 {
    let mut a = a.unsigned_abs();
    let mut b = b.unsigned_abs();
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

impl Ratio {
    pub const ZERO: Ratio = Ratio { num: 0, den: 1 };
    pub const ONE: Ratio = Ratio { num: 1, den: 1 };

    pub fn new(num: i128, den: i128) -> Result<Self, &'static str> {
        if den == 0 {
            return Err("zero denominator");
        }
        let g = gcd(num, den).max(1);
        // 2^127 fits only in u128; it divides signed values only when they
        // are 0 or i128::MIN. Avoid casting it to a negative divisor.
        let (mut n, mut d) = if g == (1u128 << 127) {
            (if num == 0 { 0 } else { -1 }, if den == 0 { 0 } else { -1 })
        } else {
            (num / (g as i128), den / (g as i128))
        };
        if d < 0 {
            n = n.checked_neg().ok_or(OVERFLOW)?;
            d = d.checked_neg().ok_or(OVERFLOW)?;
        }
        Ok(Self { num: n, den: d })
    }

    pub fn int(x: i64) -> Self {
        Self {
            num: x as i128,
            den: 1,
        }
    }

    pub fn to_f64(self) -> f64 {
        self.num as f64 / self.den as f64
    }

    pub fn is_zero(self) -> bool {
        self.num == 0
    }

    fn add(self, o: Self) -> Result<Self, &'static str> {
        let g = gcd(self.den, o.den) as i128;
        let l = self.den / g;
        let r = o.den / g;
        let num = self
            .num
            .checked_mul(r)
            .and_then(|a| o.num.checked_mul(l).and_then(|b| a.checked_add(b)))
            .ok_or(OVERFLOW)?;
        let den = self.den.checked_mul(r).ok_or(OVERFLOW)?;
        Self::new(num, den)
    }

    fn sub(self, o: Self) -> Result<Self, &'static str> {
        self.add(Self {
            num: o.num.checked_neg().ok_or(OVERFLOW)?,
            den: o.den,
        })
    }

    fn mul(self, o: Self) -> Result<Self, &'static str> {
        let g1 = gcd(self.num, o.den).max(1) as i128;
        let g2 = gcd(o.num, self.den).max(1) as i128;
        let num = (self.num / g1).checked_mul(o.num / g2).ok_or(OVERFLOW)?;
        let den = (self.den / g2).checked_mul(o.den / g1).ok_or(OVERFLOW)?;
        Self::new(num, den)
    }

    fn div(self, o: Self) -> Result<Self, &'static str> {
        if o.num == 0 {
            return Err("division by zero");
        }
        self.mul(Self::new(o.den, o.num)?)
    }

    fn signum(self) -> i128 {
        self.num.signum()
    }
}

impl PartialOrd for Ratio {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

// Compare nonnegative rationals by their continued fractions. Each step uses
// only division and remainder, and therefore cannot overflow. Inversion
// reverses the ordering at every iteration. Denominators are positive.
fn compare_unsigned_fractions(mut an: u128, mut ad: u128, mut bn: u128, mut bd: u128) -> Ordering {
    let mut reversed = false;
    loop {
        let (aq, ar) = (an / ad, an % ad);
        let (bq, br) = (bn / bd, bn % bd);
        let order = if aq != bq {
            Some(aq.cmp(&bq))
        } else if ar == 0 || br == 0 {
            Some(match (ar == 0, br == 0) {
                (true, true) => Ordering::Equal,
                (true, false) => Ordering::Less,
                (false, true) => Ordering::Greater,
                (false, false) => unreachable!(),
            })
        } else {
            None
        };
        if let Some(order) = order {
            return if reversed { order.reverse() } else { order };
        }
        (an, ad, bn, bd) = (ad, ar, bd, br);
        reversed = !reversed;
    }
}

impl Ord for Ratio {
    fn cmp(&self, other: &Self) -> Ordering {
        let signs = self.num.signum().cmp(&other.num.signum());
        if signs != Ordering::Equal {
            return signs;
        }
        if self.num == 0 {
            return Ordering::Equal;
        }
        let order = compare_unsigned_fractions(
            self.num.unsigned_abs(),
            self.den as u128,
            other.num.unsigned_abs(),
            other.den as u128,
        );
        if self.num < 0 {
            order.reverse()
        } else {
            order
        }
    }
}

/// How the returned lottery was selected on the GT optimal face.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Selection {
    /// The candidate with the smallest identifier whose margin row is
    /// non-negative (a weak Condorcet winner) receives all mass.
    WeakCondorcetWinner(usize),
    /// No weak Condorcet winner: the basic feasible solution reached by the
    /// exact phase-one simplex with Bland's rule in candidate-ID column order.
    SimplexVertex,
    /// The face is not a single point and [`Selector::MinimumNorm`] was
    /// requested: the unique point of minimum Euclidean norm on the face.
    MinimumNorm,
}

/// Which point of the GT optimal face a caller asks for.
///
/// Both selectors return the same lottery whenever the face is a single
/// point ([`FaceCertificate::nonunique`] false); they differ only on a
/// non-unique face.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Selector {
    /// The declared deterministic rule of [`aggregate_rankings`]: the first
    /// weak Condorcet winner in candidate-ID order, otherwise the exact
    /// phase-one simplex vertex. It depends on the candidate numbering.
    #[default]
    Vertex,
    /// The point of minimum Euclidean norm on the face, computed exactly.
    /// It is unique and equivariant under any relabelling of the
    /// candidates, so it favours no candidate because of its number.
    MinimumNorm,
}

/// Exact coordinate extrema over the GT optimal face.
#[derive(Debug, Clone, PartialEq)]
pub struct FaceCertificate {
    pub min: Vec<Ratio>,
    pub max: Vec<Ratio>,
    /// True iff some coordinate can vary over the optimal face, i.e. the GT
    /// equilibrium is not unique and the selection rule matters.
    pub nonunique: bool,
}

/// Lottery in candidate-ID order (`probabilities[c]` is candidate `c`).
#[derive(Debug, Clone, PartialEq)]
pub struct GeneralOutcome {
    pub candidates: usize,
    pub voters: usize,
    pub margins: Vec<Vec<i64>>,
    pub exact: Vec<Ratio>,
    pub probabilities: Vec<f64>,
    pub selection: Selection,
    pub face: FaceCertificate,
}

/// Validate complete rankings and compute the GT margin matrix. Each ballot
/// must be a permutation of `0..candidates`.
pub fn margins_from_rankings(
    ballots: &[Vec<usize>],
    candidates: usize,
) -> Result<Vec<Vec<i64>>, &'static str> {
    if candidates == 0 || candidates > MAX_CANDIDATES {
        return Err("candidate count must be between 1 and MAX_CANDIDATES");
    }
    if ballots.is_empty() {
        return Err("at least one ballot is required");
    }
    let mut margins = vec![vec![0i64; candidates]; candidates];
    for ballot in ballots {
        if ballot.len() != candidates {
            return Err("each ballot must be a complete ranking of every candidate");
        }
        let mut seen = vec![false; candidates];
        for &c in ballot {
            if c >= candidates || seen[c] {
                return Err("each ballot must rank every candidate exactly once");
            }
            seen[c] = true;
        }
        for top in 0..candidates {
            for bottom in (top + 1)..candidates {
                let (i, j) = (ballot[top], ballot[bottom]);
                margins[i][j] = margins[i][j].checked_add(1).ok_or("margin overflow")?;
                margins[j][i] = margins[j][i].checked_sub(1).ok_or("margin overflow")?;
            }
        }
    }
    Ok(margins)
}

/// Aggregate complete rankings of `candidates` alternatives with GT.
pub fn aggregate_rankings(
    ballots: &[Vec<usize>],
    candidates: usize,
) -> Result<GeneralOutcome, &'static str> {
    let margins = margins_from_rankings(ballots, candidates)?;
    let mut out = solve_margins(&margins)?;
    out.voters = ballots.len();
    Ok(out)
}

/// Solve the GT game of a skew-symmetric integer margin matrix exactly.
/// `voters` is left at zero; [`aggregate_rankings`] fills it.
pub fn solve_margins(margins: &[Vec<i64>]) -> Result<GeneralOutcome, &'static str> {
    let m = margins.len();
    if m == 0 || m > MAX_CANDIDATES {
        return Err("candidate count must be between 1 and MAX_CANDIDATES");
    }
    for i in 0..m {
        if margins[i].len() != m {
            return Err("margin matrix must be square");
        }
        if margins[i][i] != 0 {
            return Err("margin diagonal must be zero");
        }
        for j in 0..m {
            if margins[i][j].checked_neg() != Some(margins[j][i]) {
                return Err("margin matrix must be skew-symmetric");
            }
        }
    }
    let face = face_certificate(margins)?;
    let (exact, selection) = match (0..m).find(|&i| margins[i].iter().all(|&x| x >= 0)) {
        Some(w) => {
            let mut p = vec![Ratio::ZERO; m];
            p[w] = Ratio::ONE;
            (p, Selection::WeakCondorcetWinner(w))
        }
        None => (feasible_vertex(margins)?, Selection::SimplexVertex),
    };
    check_equilibrium(margins, &exact)?;
    let probabilities = exact.iter().map(|r| r.to_f64()).collect();
    Ok(GeneralOutcome {
        candidates: m,
        voters: 0,
        margins: margins.to_vec(),
        exact,
        probabilities,
        selection,
        face,
    })
}

/// [`aggregate_rankings`] with an explicit [`Selector`].
/// `Selector::Vertex` returns exactly what [`aggregate_rankings`] returns.
pub fn aggregate_rankings_with(
    ballots: &[Vec<usize>],
    candidates: usize,
    selector: Selector,
) -> Result<GeneralOutcome, &'static str> {
    let margins = margins_from_rankings(ballots, candidates)?;
    let mut out = solve_margins_with(&margins, selector)?;
    out.voters = ballots.len();
    Ok(out)
}

/// [`solve_margins`] with an explicit [`Selector`]. With
/// `Selector::MinimumNorm` on a non-unique face, `exact` and
/// `probabilities` hold the minimum-norm lottery and `selection` is
/// [`Selection::MinimumNorm`]; on a unique face the result is that of
/// [`solve_margins`], unchanged.
pub fn solve_margins_with(
    margins: &[Vec<i64>],
    selector: Selector,
) -> Result<GeneralOutcome, &'static str> {
    let mut out = solve_margins(margins)?;
    if selector == Selector::MinimumNorm && out.face.nonunique {
        let p = minimum_norm_point(margins)?;
        check_equilibrium(margins, &p)?;
        out.probabilities = p.iter().map(|r| r.to_f64()).collect();
        out.exact = p;
        out.selection = Selection::MinimumNorm;
    }
    Ok(out)
}

/// Exact Gauss-Jordan solve of the square system `a x = b`; `Ok(None)` if
/// `a` is singular.
fn solve_square(
    mut a: Vec<Vec<Ratio>>,
    mut b: Vec<Ratio>,
) -> Result<Option<Vec<Ratio>>, &'static str> {
    let r = a.len();
    for col in 0..r {
        let Some(piv) = (col..r).find(|&k| !a[k][col].is_zero()) else {
            return Ok(None);
        };
        a.swap(col, piv);
        b.swap(col, piv);
        let p = a[col][col];
        for x in a[col].iter_mut() {
            *x = x.div(p)?;
        }
        b[col] = b[col].div(p)?;
        for k in 0..r {
            if k == col || a[k][col].is_zero() {
                continue;
            }
            let f = a[k][col];
            for j in col..r {
                let v = a[col][j];
                if !v.is_zero() {
                    a[k][j] = a[k][j].sub(f.mul(v)?)?;
                }
            }
            b[k] = b[k].sub(f.mul(b[col])?)?;
        }
    }
    Ok(Some(b))
}

/// Rank of integer rows, by exact elimination.
fn rank_of(rows: &[Vec<i64>]) -> Result<usize, &'static str> {
    let mut a: Vec<Vec<Ratio>> = rows
        .iter()
        .map(|r| r.iter().map(|&x| Ratio::int(x)).collect())
        .collect();
    let cols = a.first().map_or(0, |r| r.len());
    let mut rank = 0;
    for col in 0..cols {
        let Some(piv) = (rank..a.len()).find(|&k| !a[k][col].is_zero()) else {
            continue;
        };
        a.swap(rank, piv);
        let p = a[rank][col];
        for k in 0..a.len() {
            if k == rank || a[k][col].is_zero() {
                continue;
            }
            let f = a[k][col].div(p)?;
            for j in col..cols {
                let v = a[rank][j];
                if !v.is_zero() {
                    a[k][j] = a[k][j].sub(f.mul(v)?)?;
                }
            }
        }
        rank += 1;
    }
    Ok(rank)
}

/// Divide an integer row by the gcd of its entries. A positive scaling of a
/// constraint row changes neither the constraint nor the sign of its
/// multiplier, and it keeps the exact arithmetic small.
fn primitive(row: Vec<i64>) -> Vec<i64> {
    let g = row.iter().fold(0i128, |g, &x| gcd(g, x as i128) as i128);
    if g <= 1 {
        return row;
    }
    row.into_iter().map(|x| (x as i128 / g) as i64).collect()
}

/// Exact minimum and maximum of every slack `s_j = (M^T p)_j` over the face.
fn slack_ranges(margins: &[Vec<i64>]) -> Result<(Vec<Ratio>, Vec<Ratio>), &'static str> {
    let m = margins.len();
    let base = build_phase_one(margins)?;
    let (mut lo, mut hi) = (Vec::with_capacity(m), Vec::with_capacity(m));
    for j in 0..m {
        for sign in [1i64, -1] {
            let mut t = Tableau {
                rows: base.rows.clone(),
                basis: base.basis.clone(),
                columns: base.columns,
            };
            let mut cost = vec![Ratio::ZERO; t.rows[0].len() - 1];
            cost[m + j] = Ratio::int(sign);
            t.optimize(&cost, t.columns)?;
            let v = t.solution()[m + j];
            if sign == 1 {
                lo.push(v)
            } else {
                hi.push(v)
            }
        }
    }
    Ok((lo, hi))
}

/// Advance `idx` to the next lexicographic combination of `idx.len()`
/// indices out of `0..n`; false after the last one.
fn next_combination(idx: &mut [usize], n: usize) -> bool {
    let k = idx.len();
    for i in (0..k).rev() {
        if idx[i] < n - k + i {
            idx[i] += 1;
            for j in i + 1..k {
                idx[j] = idx[j - 1] + 1;
            }
            return true;
        }
    }
    false
}

/// The unique point of minimum Euclidean norm on the GT optimal face
/// `{p >= 0, 1^T p = 1, M^T p >= 0}`, by exact enumeration of active sets.
///
/// Constraints tight on the whole face (read off the exact coordinate and
/// slack ranges) are equalities; constraints never tight on the face are
/// dropped; the others are candidates. For each active set `S` of
/// candidates (by increasing size, in index order) with linearly
/// independent rows `R`, the projection of the origin onto
/// `{equalities, a_k^T p = 0 for k in S}` is `p = R^T nu` with
/// `(R R^T) nu = e_sum`. The first `S` whose point is feasible and whose
/// multipliers on `S` are non-negative satisfies the KKT conditions of this
/// strictly convex problem, so its point is the unique minimum. Exact
/// `i128` rationals; overflow is an error, never a rounded answer.
pub fn minimum_norm_point(margins: &[Vec<i64>]) -> Result<Vec<Ratio>, &'static str> {
    let face = face_certificate(margins)?;
    let m = margins.len();
    if !face.nonunique {
        return Ok(face.min);
    }
    let (slack_lo, slack_hi) = slack_ranges(margins)?;
    let unit = |i: usize| -> Vec<i64> { (0..m).map(|k| (k == i) as i64).collect() };
    let column = |j: usize| -> Vec<i64> { primitive((0..m).map(|i| margins[i][j]).collect()) };
    let mut equalities: Vec<Vec<i64>> = vec![vec![1; m]];
    let mut candidates: Vec<Vec<i64>> = Vec::new();
    for i in 0..m {
        if face.max[i].is_zero() {
            equalities.push(unit(i));
        } else if face.min[i].is_zero() {
            candidates.push(unit(i));
        }
    }
    for j in 0..m {
        let col = column(j);
        if col.iter().all(|&x| x == 0) {
            continue; // 0 >= 0 never binds
        }
        if slack_hi[j].is_zero() {
            equalities.push(col);
        } else if slack_lo[j].is_zero() && !candidates.contains(&col) {
            candidates.push(col);
        }
    }
    // An independent subset of the equalities spans the same affine set;
    // the sum row comes first and is always kept.
    let mut basis: Vec<Vec<i64>> = Vec::new();
    for row in equalities {
        basis.push(row);
        if rank_of(&basis)? < basis.len() {
            basis.pop();
        }
    }
    let fixed = basis.len();
    let room = m.saturating_sub(fixed);
    let feasible = |p: &[Ratio]| -> Result<bool, &'static str> {
        if p.iter().any(|x| x.signum() < 0) {
            return Ok(false);
        }
        for j in 0..m {
            let mut s = Ratio::ZERO;
            for i in 0..m {
                if margins[i][j] != 0 {
                    s = s.add(p[i].mul(Ratio::int(margins[i][j]))?)?;
                }
            }
            if s.signum() < 0 {
                return Ok(false);
            }
        }
        Ok(true)
    };
    let c = candidates.len();
    for size in 0..=room.min(c) {
        let mut idx: Vec<usize> = (0..size).collect();
        loop {
            let mut rows = basis.clone();
            rows.extend(idx.iter().map(|&k| candidates[k].clone()));
            let r = rows.len();
            let mut gram = vec![vec![Ratio::ZERO; r]; r];
            for a in 0..r {
                for b in 0..r {
                    let dot: i128 = rows[a]
                        .iter()
                        .zip(&rows[b])
                        .map(|(&x, &y)| x as i128 * y as i128)
                        .sum();
                    gram[a][b] = Ratio::new(dot, 1)?;
                }
            }
            let mut rhs = vec![Ratio::ZERO; r];
            rhs[0] = Ratio::ONE;
            if let Some(nu) = solve_square(gram, rhs)? {
                if nu[fixed..].iter().all(|x| x.signum() >= 0) {
                    let mut p = vec![Ratio::ZERO; m];
                    for (row, &w) in rows.iter().zip(&nu) {
                        if w.is_zero() {
                            continue;
                        }
                        for i in 0..m {
                            if row[i] != 0 {
                                p[i] = p[i].add(w.mul(Ratio::int(row[i]))?)?;
                            }
                        }
                    }
                    if feasible(&p)? {
                        return Ok(p);
                    }
                }
            }
            if !next_combination(&mut idx, c) {
                break;
            }
        }
    }
    Err("minimum-norm point not found (should be impossible)")
}

/// Exact check that `p` is a lottery and `p^T M >= 0` column-wise.
pub fn check_equilibrium(margins: &[Vec<i64>], p: &[Ratio]) -> Result<(), &'static str> {
    let m = margins.len();
    if p.len() != m || p.iter().any(|x| x.signum() < 0) {
        return Err("lottery must be non-negative with one entry per candidate");
    }
    let mut total = Ratio::ZERO;
    for x in p {
        total = total.add(*x)?;
    }
    if total != Ratio::ONE {
        return Err("lottery must sum to one");
    }
    for j in 0..m {
        let mut payoff = Ratio::ZERO;
        for i in 0..m {
            payoff = payoff.add(p[i].mul(Ratio::int(margins[i][j]))?)?;
        }
        if payoff.signum() < 0 {
            return Err("lottery violates a GT equilibrium inequality");
        }
    }
    Ok(())
}

/// Standard-form tableau for `A x = b, x >= 0` with
/// `x = [p_0..p_{m-1}, s_0..s_{m-1}]`, rows `M^T p - s = 0` and `1^T p = 1`.
struct Tableau {
    rows: Vec<Vec<Ratio>>, // coefficients followed by rhs
    basis: Vec<usize>,
    columns: usize, // original columns, excluding artificials
}

fn build_phase_one(margins: &[Vec<i64>]) -> Result<Tableau, &'static str> {
    let m = margins.len();
    let n = 2 * m;
    let r = m + 1;
    let width = n + r + 1;
    let mut rows = vec![vec![Ratio::ZERO; width]; r];
    for j in 0..m {
        for i in 0..m {
            rows[j][i] = Ratio::int(margins[i][j]);
        }
        rows[j][m + j] = Ratio::int(-1);
    }
    for i in 0..m {
        rows[m][i] = Ratio::ONE;
    }
    rows[m][width - 1] = Ratio::ONE;
    for k in 0..r {
        rows[k][n + k] = Ratio::ONE;
    }
    let mut t = Tableau {
        rows,
        basis: (n..n + r).collect(),
        columns: n,
    };
    // Phase one: minimize the sum of artificials.
    let mut cost = vec![Ratio::ZERO; n + r];
    for c in cost.iter_mut().skip(n) {
        *c = Ratio::ONE;
    }
    t.optimize(&cost, n + r)?;
    let value = t.objective(&cost)?;
    if !value.is_zero() {
        return Err("GT optimal face is empty (should be impossible for a skew-symmetric game)");
    }
    // Drive degenerate artificials out of the basis, dropping redundant rows.
    let mut k = 0;
    while k < t.rows.len() {
        if t.basis[k] >= n {
            match (0..n).find(|&j| !t.rows[k][j].is_zero()) {
                Some(j) => t.pivot(k, j)?,
                None => {
                    t.rows.remove(k);
                    t.basis.remove(k);
                    continue;
                }
            }
        }
        k += 1;
    }
    Ok(t)
}

impl Tableau {
    fn rhs(&self, k: usize) -> Ratio {
        *self.rows[k].last().unwrap()
    }

    fn objective(&self, cost: &[Ratio]) -> Result<Ratio, &'static str> {
        let mut z = Ratio::ZERO;
        for (k, &b) in self.basis.iter().enumerate() {
            z = z.add(cost[b].mul(self.rhs(k))?)?;
        }
        Ok(z)
    }

    fn pivot(&mut self, row: usize, col: usize) -> Result<(), &'static str> {
        let p = self.rows[row][col];
        for x in self.rows[row].iter_mut() {
            *x = x.div(p)?;
        }
        let pivot_row = self.rows[row].clone();
        for (k, r) in self.rows.iter_mut().enumerate() {
            if k == row || r[col].is_zero() {
                continue;
            }
            let f = r[col];
            for (x, y) in r.iter_mut().zip(&pivot_row) {
                if !y.is_zero() {
                    *x = x.sub(f.mul(*y)?)?;
                }
            }
        }
        self.basis[row] = col;
        Ok(())
    }

    /// Minimize `cost` over columns `0..allowed` with Bland's rule.
    fn optimize(&mut self, cost: &[Ratio], allowed: usize) -> Result<(), &'static str> {
        for _ in 0..10_000 {
            let mut entering = None;
            for j in 0..allowed {
                if self.basis.contains(&j) {
                    continue;
                }
                let mut d = cost[j];
                for (k, &b) in self.basis.iter().enumerate() {
                    if !self.rows[k][j].is_zero() {
                        d = d.sub(cost[b].mul(self.rows[k][j])?)?;
                    }
                }
                if d.signum() < 0 {
                    entering = Some(j);
                    break;
                }
            }
            let Some(j) = entering else { return Ok(()) };
            let mut leave: Option<(usize, Ratio)> = None;
            for k in 0..self.rows.len() {
                let a = self.rows[k][j];
                if a.signum() <= 0 {
                    continue;
                }
                let ratio = self.rhs(k).div(a)?;
                leave = match leave {
                    None => Some((k, ratio)),
                    Some((best, br)) => match ratio.cmp(&br) {
                        Ordering::Less => Some((k, ratio)),
                        Ordering::Equal if self.basis[k] < self.basis[best] => Some((k, ratio)),
                        _ => Some((best, br)),
                    },
                };
            }
            let Some((row, _)) = leave else {
                return Err("unbounded GT linear program");
            };
            self.pivot(row, j)?;
        }
        Err("simplex iteration limit reached")
    }

    fn solution(&self) -> Vec<Ratio> {
        let mut x = vec![Ratio::ZERO; self.columns];
        for (k, &b) in self.basis.iter().enumerate() {
            if b < self.columns {
                x[b] = self.rhs(k);
            }
        }
        x
    }
}

fn feasible_vertex(margins: &[Vec<i64>]) -> Result<Vec<Ratio>, &'static str> {
    let m = margins.len();
    Ok(build_phase_one(margins)?.solution()[..m].to_vec())
}

/// Minimize and maximize every coordinate over the GT optimal face.
pub fn face_certificate(margins: &[Vec<i64>]) -> Result<FaceCertificate, &'static str> {
    let m = margins.len();
    let base = build_phase_one(margins)?;
    let mut min = Vec::with_capacity(m);
    let mut max = Vec::with_capacity(m);
    for i in 0..m {
        for sign in [1i64, -1] {
            let mut t = Tableau {
                rows: base.rows.clone(),
                basis: base.basis.clone(),
                columns: base.columns,
            };
            let mut cost = vec![Ratio::ZERO; t.rows[0].len() - 1];
            cost[i] = Ratio::int(sign);
            t.optimize(&cost, t.columns)?;
            let v = t.solution()[i];
            if sign == 1 {
                min.push(v)
            } else {
                max.push(v)
            }
        }
    }
    let nonunique = min.iter().zip(&max).any(|(a, b)| a != b);
    Ok(FaceCertificate {
        min,
        max,
        nonunique,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::aggregate;

    fn permutations(m: usize) -> Vec<Vec<usize>> {
        fn rec(prefix: &mut Vec<usize>, m: usize, out: &mut Vec<Vec<usize>>) {
            if prefix.len() == m {
                out.push(prefix.clone());
                return;
            }
            for c in 0..m {
                if !prefix.contains(&c) {
                    prefix.push(c);
                    rec(prefix, m, out);
                    prefix.pop();
                }
            }
        }
        let mut out = Vec::new();
        rec(&mut Vec::new(), m, &mut out);
        out
    }

    #[test]
    fn ratio_order_is_exact_even_when_products_overflow() {
        let max = i128::MAX;
        // Cross products exceed i128 and both values round to the same f64.
        let a = Ratio {
            num: max - 1,
            den: max,
        };
        let b = Ratio {
            num: max - 2,
            den: max - 1,
        };
        assert_eq!(a.to_f64(), b.to_f64());
        assert!(a > b);
        assert!(
            Ratio {
                num: -(max - 1),
                den: max
            } < Ratio {
                num: -(max - 2),
                den: max - 1
            }
        );
        let min = Ratio {
            num: i128::MIN,
            den: max,
        };
        let next = Ratio {
            num: -max,
            den: max - 1,
        };
        assert!(min > next);
        assert!(min < Ratio::ZERO);
        assert_eq!(min.cmp(&min), Ordering::Equal);
        assert!(
            Ratio {
                num: i128::MIN,
                den: 1
            } < Ratio { num: -max, den: 1 }
        );
    }

    #[test]
    fn ratio_constructor_handles_minimum_integer_without_panicking() {
        assert_eq!(
            Ratio::new(i128::MIN, 1),
            Ok(Ratio {
                num: i128::MIN,
                den: 1
            })
        );
        assert_eq!(Ratio::new(i128::MIN, i128::MIN), Ok(Ratio::ONE));
        assert_eq!(Ratio::new(0, i128::MIN), Ok(Ratio::ZERO));
        assert_eq!(Ratio::new(1, i128::MIN), Err(OVERFLOW));
        assert_eq!(Ratio::new(i128::MIN, -1), Err(OVERFLOW));
        assert_eq!(
            Ratio::new(i128::MIN, 2),
            Ok(Ratio {
                num: i128::MIN / 2,
                den: 1
            })
        );
        assert_eq!(
            Ratio::new(i128::MIN, 1).unwrap().mul(Ratio::ONE),
            Ok(Ratio {
                num: i128::MIN,
                den: 1
            })
        );
    }

    #[test]
    fn ratio_order_matches_cross_products_for_small_signed_values() {
        for a in -8i128..=8 {
            for b in 1i128..=8 {
                for c in -8i128..=8 {
                    for d in 1i128..=8 {
                        let x = Ratio { num: a, den: b };
                        let y = Ratio { num: c, den: d };
                        assert_eq!(x.cmp(&y), (a * d).cmp(&(c * b)));
                    }
                }
            }
        }
    }

    #[test]
    fn three_candidates_match_the_restricted_adapter_bit_for_bit() {
        let ranks = permutations(3);
        for voters in 1..=5usize {
            for code in 0..6usize.pow(voters as u32) {
                let mut x = code;
                let mut profile = Vec::new();
                let mut fixed = Vec::new();
                for _ in 0..voters {
                    let r = ranks[x % 6].clone();
                    x /= 6;
                    fixed.push([r[0], r[1], r[2]]);
                    profile.push(r);
                }
                let general = aggregate_rankings(&profile, 3).unwrap();
                let three = aggregate(&fixed).unwrap();
                assert_eq!(
                    general.probabilities,
                    three.probabilities.to_vec(),
                    "{profile:?}"
                );
                for i in 0..3 {
                    assert_eq!(general.margins[i], three.margins[i].to_vec());
                }
                if voters % 2 == 1 {
                    assert!(!general.face.nonunique, "{profile:?}");
                }
            }
        }
    }

    #[test]
    fn odd_profiles_of_four_and_five_candidates_have_unique_certified_lotteries() {
        for m in [4usize, 5] {
            let ranks = permutations(m);
            let mut state = 0x9e37_79b9_7f4a_7c15u64;
            for _ in 0..300 {
                let mut profile = Vec::new();
                for _ in 0..(1 + 2 * (state % 4) as usize) {
                    state ^= state << 13;
                    state ^= state >> 7;
                    state ^= state << 17;
                    profile.push(ranks[(state % ranks.len() as u64) as usize].clone());
                }
                let out = aggregate_rankings(&profile, m).unwrap();
                check_equilibrium(&out.margins, &out.exact).unwrap();
                assert!(!out.face.nonunique, "{profile:?}");
                assert_eq!(out.face.min, out.exact);
                // Odd skew-symmetric games have an odd-sized support.
                assert_eq!(out.exact.iter().filter(|x| !x.is_zero()).count() % 2, 1);
            }
        }
    }

    #[test]
    fn four_cycle_with_ties_has_a_certified_nonunique_face() {
        // Two ballots: 0>1>2>3 and 3>2>1>0 tie every pair: the whole simplex
        // is optimal and the first weak Condorcet winner (0) is selected.
        let out = aggregate_rankings(&[vec![0, 1, 2, 3], vec![3, 2, 1, 0]], 4).unwrap();
        assert_eq!(out.selection, Selection::WeakCondorcetWinner(0));
        assert!(out.face.nonunique);
        assert!(out.face.min.iter().all(|x| x.is_zero()));
        assert!(out.face.max.iter().all(|x| *x == Ratio::ONE));
    }

    #[test]
    fn simplex_vertex_is_used_without_a_weak_condorcet_winner() {
        // A strict 3-cycle among 0, 1, 2 plus a candidate 3 beaten by all:
        // no row is non-negative, so the exact simplex vertex is returned.
        let m = vec![
            vec![0, 1, -1, 1],
            vec![-1, 0, 1, 1],
            vec![1, -1, 0, 1],
            vec![-1, -1, -1, 0],
        ];
        let out = solve_margins(&m).unwrap();
        assert_eq!(out.selection, Selection::SimplexVertex);
        let third = Ratio::new(1, 3).unwrap();
        assert_eq!(out.exact, vec![third, third, third, Ratio::ZERO]);
        assert!(!out.face.nonunique);
    }

    fn r(n: i128, d: i128) -> Ratio {
        Ratio::new(n, d).unwrap()
    }

    #[test]
    fn minimum_norm_hand_worked_faces() {
        // Full tie (every margin zero): the face is the whole simplex; the
        // vertex rule gives candidate 0 everything, the minimum-norm point is
        // uniform.
        let tie = aggregate_rankings_with(
            &[vec![0, 1, 2, 3], vec![3, 2, 1, 0]],
            4,
            Selector::MinimumNorm,
        )
        .unwrap();
        assert_eq!(tie.selection, Selection::MinimumNorm);
        assert_eq!(tie.exact, vec![r(1, 4); 4]);
        // Two weak Condorcet winners 0 and 1 tied with each other, both
        // beating 2: the face is the segment [e0, e1]; minimum norm is its
        // midpoint, the vertex rule picks 0.
        let ballots = vec![vec![0, 1, 2], vec![1, 0, 2]];
        let v = aggregate_rankings_with(&ballots, 3, Selector::Vertex).unwrap();
        let b = aggregate_rankings_with(&ballots, 3, Selector::MinimumNorm).unwrap();
        assert_eq!(v.exact, vec![Ratio::ONE, Ratio::ZERO, Ratio::ZERO]);
        assert_eq!(b.exact, vec![r(1, 2), r(1, 2), Ratio::ZERO]);
        assert_eq!(v.face, b.face);
        // The differential test's fixed four-ballot degenerate profile:
        // checked against the certificate and the equilibrium inequalities.
        let ballots = vec![
            vec![2, 0, 3, 1],
            vec![1, 3, 0, 2],
            vec![0, 1, 2, 3],
            vec![3, 2, 1, 0],
        ];
        let b = aggregate_rankings_with(&ballots, 4, Selector::MinimumNorm).unwrap();
        check_equilibrium(&b.margins, &b.exact).unwrap();
        for i in 0..4 {
            assert!(b.face.min[i] <= b.exact[i] && b.exact[i] <= b.face.max[i]);
        }
    }

    fn norm2(p: &[Ratio]) -> Ratio {
        p.iter()
            .fold(Ratio::ZERO, |s, x| s.add(x.mul(*x).unwrap()).unwrap())
    }

    /// Every face point is a convex combination of face vertices; checking
    /// optimality along the segment from the minimum-norm point to each
    /// coordinate's extreme vertices is a necessary condition: no feasible
    /// direction decreases the norm (first-order condition <p, v - p> >= 0).
    fn assert_first_order(margins: &[Vec<i64>], p: &[Ratio]) {
        let m = margins.len();
        let base = build_phase_one(margins).unwrap();
        for i in 0..m {
            for sign in [1i64, -1] {
                let mut t = Tableau {
                    rows: base.rows.clone(),
                    basis: base.basis.clone(),
                    columns: base.columns,
                };
                let mut cost = vec![Ratio::ZERO; t.rows[0].len() - 1];
                cost[i] = Ratio::int(sign);
                t.optimize(&cost, t.columns).unwrap();
                let v = &t.solution()[..m];
                let mut inner = Ratio::ZERO;
                for k in 0..m {
                    inner = inner
                        .add(p[k].mul(v[k].sub(p[k]).unwrap()).unwrap())
                        .unwrap();
                }
                assert!(inner.signum() >= 0, "{margins:?} {p:?} {v:?}");
            }
        }
    }

    #[test]
    fn minimum_norm_is_optimal_neutral_and_agrees_on_unique_faces() {
        let mut state = 0x2545_f491_4f6c_dd1du64;
        let mut next = || {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            state
        };
        let mut nonunique = 0;
        for m in 2..=6usize {
            let ranks = permutations(m);
            for _ in 0..120 {
                let voters = 2 + 2 * (next() % 3) as usize; // even: ties possible
                let profile: Vec<Vec<usize>> = (0..voters)
                    .map(|_| ranks[(next() % ranks.len() as u64) as usize].clone())
                    .collect();
                let v = aggregate_rankings_with(&profile, m, Selector::Vertex).unwrap();
                assert_eq!(v, aggregate_rankings(&profile, m).unwrap());
                let b = aggregate_rankings_with(&profile, m, Selector::MinimumNorm).unwrap();
                check_equilibrium(&b.margins, &b.exact).unwrap();
                if !v.face.nonunique {
                    assert_eq!(b, v);
                    continue;
                }
                nonunique += 1;
                assert_eq!(b.selection, Selection::MinimumNorm);
                assert!(norm2(&b.exact) <= norm2(&v.exact));
                assert_first_order(&b.margins, &b.exact);
                // Neutrality: relabel candidates by a cyclic shift; the
                // minimum-norm lottery is relabelled the same way.
                let shift = 1 + (next() % (m as u64 - 1)) as usize;
                let relabelled: Vec<Vec<usize>> = profile
                    .iter()
                    .map(|b| b.iter().map(|&c| (c + shift) % m).collect())
                    .collect();
                let b2 = aggregate_rankings_with(&relabelled, m, Selector::MinimumNorm).unwrap();
                for c in 0..m {
                    assert_eq!(b2.exact[(c + shift) % m], b.exact[c]);
                }
            }
        }
        assert!(nonunique > 50, "{nonunique}");
    }

    #[test]
    fn minimum_norm_handles_eight_candidates() {
        let ranks = permutations(8);
        let mut state = 0x9e37_79b9_7f4a_7c15u64;
        for _ in 0..20 {
            let profile: Vec<Vec<usize>> = (0..4)
                .map(|_| {
                    state ^= state << 13;
                    state ^= state >> 7;
                    state ^= state << 17;
                    ranks[(state % ranks.len() as u64) as usize].clone()
                })
                .collect();
            let b = aggregate_rankings_with(&profile, 8, Selector::MinimumNorm).unwrap();
            check_equilibrium(&b.margins, &b.exact).unwrap();
        }
    }

    #[test]
    fn invalid_inputs_are_rejected() {
        assert!(aggregate_rankings(&[], 3).is_err());
        assert!(aggregate_rankings(&[vec![0, 1]], 3).is_err());
        assert!(aggregate_rankings(&[vec![0, 1, 1]], 3).is_err());
        assert!(aggregate_rankings(&[vec![0, 1, 3]], 3).is_err());
        assert!(aggregate_rankings(&[vec![0]], 0).is_err());
        let too_many: Vec<usize> = (0..=MAX_CANDIDATES).collect();
        assert!(aggregate_rankings(&[too_many], MAX_CANDIDATES + 1).is_err());
        assert!(solve_margins(&[vec![0, 1], vec![0, 0]]).is_err());
        assert!(solve_margins(&[vec![1]]).is_err());
        let single = aggregate_rankings(&[vec![0]], 1).unwrap();
        assert_eq!(single.probabilities, vec![1.0]);
        let pair = aggregate_rankings(&[vec![1, 0], vec![1, 0], vec![0, 1]], 2).unwrap();
        assert_eq!(pair.probabilities, vec![0.0, 1.0]);
    }
}
