use gtiv_three::aggregate;

fn main() {
    let mut ballots = Vec::new();
    for arg in std::env::args().skip(1) {
        let digits: Vec<_> = arg
            .chars()
            .map(|c| c.to_digit(10).map(|x| x as usize))
            .collect();
        if digits.len() != 3 || digits.iter().any(|x| x.is_none()) {
            eprintln!("Each ballot must be three digits, e.g. 012");
            std::process::exit(2);
        }
        ballots.push([digits[0].unwrap(), digits[1].unwrap(), digits[2].unwrap()]);
    }
    match aggregate(&ballots) {
        Ok(out) => println!(
            "{:.17} {:.17} {:.17}",
            out.probabilities[0], out.probabilities[1], out.probabilities[2]
        ),
        Err(error) => {
            eprintln!("{error}");
            std::process::exit(2);
        }
    }
}
