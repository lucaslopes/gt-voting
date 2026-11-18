//! Generate synthetic sampled rounds for the web model's parity tests.
use gtiv_three::{clique, Arms, Assembly, SplitMix64, VoterParams};

fn main() -> Result<(), &'static str> {
    let story = [vec![1; 7], vec![3; 7], vec![0]].concat();
    let cycle = [0, 3, 4].repeat(5);
    let cases = [
        ("story-high-loyalty", &story, "everyone", 0.98, 0.2, 10.0, 3),
        ("story-balanced", &story, "everyone", 0.5, 0.5, 10.0, 11),
        ("cycle-volatile", &cycle, "everyone", 0.2, 0.7, 25.0, 5),
        ("story-circle", &story, "circle", 0.3, 0.4, 15.0, 8),
    ];
    println!(r#"{{"source":"gtiv_three::Assembly","cases":["#);
    for (case_index, (name, hearts, network, alpha, eta, beta, seed)) in
        cases.into_iter().enumerate()
    {
        let n = hearts.len();
        let neighbours = if network == "circle" {
            (0..n)
                .map(|i| [1, 2, n - 1, n - 2].map(|offset| (i + offset) % n).to_vec())
                .collect()
        } else {
            clique(n)
        };
        let params = vec![VoterParams::new(alpha, beta, eta)?; n];
        let mut assembly = Assembly::new(3, hearts.clone(), params, neighbours, Arms::FEEDBACK)?;
        let mut rng = SplitMix64::new(seed);
        if case_index > 0 {
            println!(",");
        }
        println!(
            r#"{{"name":"{name}","hearts":{hearts:?},"network":"{network}","alpha":{alpha},"eta":{eta},"beta":{beta},"rounds":["#
        );
        for round_index in 0..12 {
            let before = assembly.tendencies().to_vec();
            let round = assembly.step(&mut rng)?;
            if round_index > 0 {
                println!(",");
            }
            print!(
                r#"{{"xBefore":{before:?},"reports":{:?},"p":{:?},"xAfter":{:?}}}"#,
                round.reports,
                round.published.probabilities,
                assembly.tendencies()
            );
        }
        print!("]}}");
    }
    println!("]}}");
    Ok(())
}
