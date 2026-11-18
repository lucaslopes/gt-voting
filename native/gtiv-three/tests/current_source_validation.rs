use gtiv_three::{aggregate_rankings, check_equilibrium, solve_margins, Ratio};

#[test]
fn malformed_profiles_have_stable_errors() {
    assert_eq!(
        aggregate_rankings(&[], 3).unwrap_err(),
        "at least one ballot is required"
    );
    assert_eq!(
        aggregate_rankings(&[vec![0, 1]], 3).unwrap_err(),
        "each ballot must be a complete ranking of every candidate"
    );
    assert_eq!(
        aggregate_rankings(&[vec![0, 0, 2]], 3).unwrap_err(),
        "each ballot must rank every candidate exactly once"
    );
    assert_eq!(
        aggregate_rankings(&[vec![0, 1, 3]], 3).unwrap_err(),
        "each ballot must rank every candidate exactly once"
    );
    assert_eq!(
        aggregate_rankings(&[vec![0]], 0).unwrap_err(),
        "candidate count must be between 1 and MAX_CANDIDATES"
    );
    assert_eq!(
        aggregate_rankings(&[(0..9).collect()], 9).unwrap_err(),
        "candidate count must be between 1 and MAX_CANDIDATES"
    );
}

fn extreme_skew_matrix(size: usize, seed: u64) -> Vec<Vec<i64>> {
    let mut state = seed;
    let mut matrix = vec![vec![0; size]; size];
    for i in 0..size {
        for j in (i + 1)..size {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            let magnitude = i64::MAX - (state % 4096) as i64;
            let value = if state & 1 == 0 {
                magnitude
            } else {
                -magnitude
            };
            matrix[i][j] = value;
            matrix[j][i] = -value;
        }
    }
    matrix
}

#[test]
fn extreme_margin_matrices_return_exact_results_or_documented_overflow() {
    for size in [3, 4, 5, 6, 8] {
        for seed in [0x9e37_79b9_7f4a_7c15, 0x2545_f491_4f6c_dd1d] {
            let margins = extreme_skew_matrix(size, seed ^ size as u64);
            match solve_margins(&margins) {
                Ok(outcome) => {
                    check_equilibrium(&margins, &outcome.exact).unwrap();
                    assert_eq!(
                        outcome.exact.iter().map(|x| x.to_f64()).collect::<Vec<_>>(),
                        outcome.probabilities
                    );
                }
                Err(error) => assert_eq!(error, "exact arithmetic overflow"),
            }
        }
    }
}

#[test]
fn exact_rational_contract_has_positive_denominators() {
    for numerator in -16..=16 {
        for denominator in 1..=16 {
            let value = Ratio::new(numerator, denominator).unwrap();
            assert!(value.den > 0);
            assert_eq!(value.num * denominator, numerator * value.den);
        }
    }
}
