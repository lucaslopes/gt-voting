//! A native, three-alternative Rivest-Shen GT adapter.
//!
//! The margin convention and equilibrium condition follow the Python `GT`
//! mechanism. The restricted adapter accepts complete rankings of exactly
//! three alternatives. The `general` implementation supports up to eight.
//! It selects the first weak Condorcet winner when available; otherwise the
//! unique strict three-cycle has an analytic zero-sum equilibrium. On a
//! degenerate optimal face its selection may differ from SciPy/HiGHS. The
//! returned indices are candidate identifiers 0, 1, 2; the Python GT API
//! returns values in the order candidates appear in the first ballot.

mod dynamics;
mod general;
pub use dynamics::{
    clique, draw_ranking, logit_response, scores, update_tendency, Arms, Assembly, Channel,
    RankingSpace, ReplayUniforms, Round, SplitMix64, UniformSource, VoterParams, SOFTMAX_FLOOR,
};
pub use general::{
    aggregate_rankings, aggregate_rankings_with, check_equilibrium, face_certificate,
    margins_from_rankings, minimum_norm_point, solve_margins, solve_margins_with, FaceCertificate,
    GeneralOutcome, Ratio, Selection, Selector, MAX_CANDIDATES,
};

#[derive(Debug, Clone, PartialEq)]
pub struct Outcome {
    pub margins: [[i64; 3]; 3],
    pub probabilities: [f64; 3],
}

/// Aggregate complete rankings in candidate order. Each ballot must be a
/// permutation of 0, 1, 2. Returns an error on an empty or invalid profile.
pub fn aggregate(ballots: &[[usize; 3]]) -> Result<Outcome, &'static str> {
    if ballots.is_empty() {
        return Err("at least one ballot is required");
    }
    let mut margins = [[0i64; 3]; 3];
    for ballot in ballots {
        let mut seen = [false; 3];
        for &candidate in ballot {
            if candidate >= 3 || seen[candidate] {
                return Err("each ballot must rank candidates 0, 1, 2 exactly once");
            }
            seen[candidate] = true;
        }
        for top in 0..3 {
            for bottom in (top + 1)..3 {
                let i = ballot[top];
                let j = ballot[bottom];
                margins[i][j] = margins[i][j].checked_add(1).ok_or("margin overflow")?;
                margins[j][i] = margins[j][i].checked_sub(1).ok_or("margin overflow")?;
            }
        }
    }
    let probabilities = solve_three(margins)?;
    Ok(Outcome {
        margins,
        probabilities,
    })
}

/// Compute a probability vector p such that p^T M >= 0 for every column.
/// This explicitly implements only skew-symmetric 3-by-3 margin games.
pub fn solve_three(margins: [[i64; 3]; 3]) -> Result<[f64; 3], &'static str> {
    for i in 0..3 {
        if margins[i][i] != 0 {
            return Err("margin diagonal must be zero");
        }
        for j in 0..3 {
            if margins[i][j].checked_neg() != Some(margins[j][i]) {
                return Err("margin matrix must be skew-symmetric");
            }
        }
    }
    for i in 0..3 {
        if margins[i].iter().all(|&value| value >= 0) {
            let mut p = [0.0; 3];
            p[i] = 1.0;
            return Ok(p);
        }
    }
    let mut weights = [
        margins[1][2] as f64,
        margins[2][0] as f64,
        margins[0][1] as f64,
    ];
    if weights.iter().all(|x| *x < 0.0) {
        for x in &mut weights {
            *x = -*x;
        }
    }
    if weights.iter().any(|x| *x <= 0.0) {
        return Err("no supported three-candidate equilibrium");
    }
    let total = weights.iter().sum::<f64>();
    Ok(weights.map(|x| x / total))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn feasible(out: &Outcome) {
        assert!((out.probabilities.iter().sum::<f64>() - 1.0).abs() < 1e-12);
        assert!(out.probabilities.iter().all(|x| *x >= 0.0));
        for j in 0..3 {
            let payoff: f64 = (0..3)
                .map(|i| out.probabilities[i] * out.margins[i][j] as f64)
                .sum();
            assert!(payoff >= -1e-10, "column {j}: {payoff}");
        }
    }

    #[test]
    fn symmetric_cycle_returns_equal_lottery() {
        let out = aggregate(&[[0, 1, 2], [1, 2, 0], [2, 0, 1]]).unwrap();
        feasible(&out);
        for p in out.probabilities {
            assert!((p - 1.0 / 3.0).abs() < 1e-12);
        }
    }

    #[test]
    fn condorcet_winner_gets_all_mass() {
        let out = aggregate(&[[0, 1, 2], [0, 2, 1], [1, 0, 2]]).unwrap();
        feasible(&out);
        assert_eq!(out.probabilities, [1.0, 0.0, 0.0]);
    }

    #[test]
    fn every_profile_of_exactly_six_ballots_is_feasible() {
        let ranks = [
            [0, 1, 2],
            [0, 2, 1],
            [1, 0, 2],
            [1, 2, 0],
            [2, 0, 1],
            [2, 1, 0],
        ];
        for code in 0..6usize.pow(6) {
            let mut x = code;
            let mut profile = [[0; 3]; 6];
            for ballot in &mut profile {
                *ballot = ranks[x % 6];
                x /= 6;
            }
            feasible(&aggregate(&profile).unwrap());
        }
    }

    #[test]
    fn malformed_ballots_and_nonskew_games_are_rejected() {
        assert!(aggregate(&[]).is_err());
        assert!(aggregate(&[[0, 0, 1]]).is_err());
        assert!(aggregate(&[[0, 1, 3]]).is_err());
        assert!(solve_three([[0, 1, 0], [0, 0, 0], [0, 0, 0]]).is_err());
    }
}
