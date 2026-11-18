use gtiv_three::{
    clique, Arms, Assembly, RankingSpace, Ratio, ReplayUniforms, Selector, VoterParams,
};

fn binary_assembly(arms: Arms) -> Assembly {
    let parameters = VoterParams::new(0.0, 1.0, 1.0).unwrap();
    Assembly::new(2, vec![0, 0, 1], vec![parameters; 3], clique(3), arms).unwrap()
}

#[test]
fn a_cycle_produces_the_exact_lottery_in_candidate_id_order() {
    let space = RankingSpace::new(3).unwrap();
    let reports = [[2, 0, 1], [0, 1, 2], [1, 2, 0]]
        .iter()
        .map(|ranking| space.index_of(ranking).unwrap())
        .collect::<Vec<_>>();
    let parameters = VoterParams::new(0.2, 1.0, 0.3).unwrap();
    let mut assembly = Assembly::new(
        3,
        reports.clone(),
        vec![parameters; 3],
        clique(3),
        Arms::FEEDBACK,
    )
    .unwrap();
    let round = assembly.step_with_reports(&reports).unwrap();
    assert_eq!(round.index, 0);
    assert_eq!(round.reports, reports);
    assert_eq!(round.published.exact, vec![Ratio::new(1, 3).unwrap(); 3]);
    assert_eq!(round.display, round.published.probabilities);
}

#[test]
fn fixed_and_live_displays_share_the_published_lottery_but_change_feedback() {
    let mut live = binary_assembly(Arms::FEEDBACK);
    let mut fixed = binary_assembly(Arms::BOTH_FIXED);
    let reports = [1, 1, 1];
    let live_round = live.step_with_reports(&reports).unwrap();
    let fixed_round = fixed.step_with_reports(&reports).unwrap();

    assert_eq!(live_round.published, fixed_round.published);
    assert_eq!(live_round.published.exact, [Ratio::ZERO, Ratio::ONE]);
    assert_eq!(live_round.display, [0.0, 1.0]);
    assert_eq!(fixed_round.display, [1.0, 0.0]);
    assert!(live.tendency(0)[1] > 0.5);
    assert!(fixed.tendency(0)[1] < 0.5);
    for state in [live.tendencies(), fixed.tendencies()] {
        for tendency in state {
            assert!((tendency.iter().sum::<f64>() - 1.0).abs() < 1e-12);
        }
    }
}

#[test]
fn an_invalid_report_preserves_state_and_the_caller_controls_sampling() {
    let mut assembly = binary_assembly(Arms::FEEDBACK);
    assembly.set_selector(Selector::MinimumNorm).unwrap();
    assembly.set_tendency(0, vec![0.25, 0.75]).unwrap();
    let before = assembly.tendencies().to_vec();
    assert!(assembly.step_with_reports(&[0, 1, 2]).is_err());
    assert_eq!(assembly.rounds(), 0);
    assert_eq!(assembly.tendencies(), before);

    let mut uniforms = ReplayUniforms::new(vec![0.25, 0.0, 0.5]);
    let round = assembly.step(&mut uniforms).unwrap();
    assert_eq!(uniforms.consumed(), 3);
    assert_eq!(round.reports, [1, 0, 1]);
    assert_eq!(round.published.exact, [Ratio::ZERO, Ratio::ONE]);
    assert_eq!(assembly.rounds(), 1);
}

#[test]
fn the_minimum_norm_selector_returns_equal_weights_on_a_tie() {
    let parameters = VoterParams::new(1.0, 0.0, 1.0).unwrap();
    let mut assembly = Assembly::new(
        2,
        vec![0, 1],
        vec![parameters; 2],
        clique(2),
        Arms::FEEDBACK,
    )
    .unwrap();
    assembly.set_selector(Selector::MinimumNorm).unwrap();
    let round = assembly.step_with_reports(&[1, 0]).unwrap();

    assert_eq!(round.published.exact, vec![Ratio::new(1, 2).unwrap(); 2]);
    assert_eq!(assembly.tendencies(), &[vec![1.0, 0.0], vec![0.0, 1.0]]);
}
