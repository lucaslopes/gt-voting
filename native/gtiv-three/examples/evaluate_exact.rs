//! Validation runner: read `m ballot ballot ...` lines and return the exact
//! rational outcomes and face certificates for both supported selectors.
use gtiv_three::{aggregate_rankings_with, GeneralOutcome, Ratio, Selection, Selector};
use std::io::{self, BufRead, Write};

fn fractions(values: &[Ratio]) -> String {
    values
        .iter()
        .map(|x| format!("{}/{}", x.num, x.den))
        .collect::<Vec<_>>()
        .join(",")
}

fn selection(outcome: &GeneralOutcome) -> String {
    match outcome.selection {
        Selection::WeakCondorcetWinner(candidate) => format!("weak_condorcet:{candidate}"),
        Selection::SimplexVertex => "simplex_vertex".into(),
        Selection::MinimumNorm => "minimum_norm".into(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.expect("stdin");
        let mut fields = line.split_whitespace();
        let Some(m) = fields.next().and_then(|x| x.parse::<usize>().ok()) else {
            writeln!(out, "ERROR\tmissing candidate count").unwrap();
            continue;
        };
        let ballots: Option<Vec<Vec<usize>>> = fields
            .map(|ballot| {
                ballot
                    .chars()
                    .map(|c| c.to_digit(10).map(|x| x as usize))
                    .collect()
            })
            .collect();
        let Some(ballots) = ballots else {
            writeln!(out, "ERROR\tballots must contain candidate digits").unwrap();
            continue;
        };

        match (
            aggregate_rankings_with(&ballots, m, Selector::Vertex),
            aggregate_rankings_with(&ballots, m, Selector::MinimumNorm),
        ) {
            (Ok(vertex), Ok(minimum_norm)) => {
                writeln!(
                    out,
                    "OK\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
                    fractions(&vertex.exact),
                    fractions(&minimum_norm.exact),
                    fractions(&vertex.face.min),
                    fractions(&vertex.face.max),
                    vertex.face.nonunique,
                    selection(&vertex),
                    selection(&minimum_norm),
                )
                .unwrap();
            }
            (Err(error), _) | (_, Err(error)) => {
                writeln!(out, "ERROR\t{error}").unwrap();
            }
        }
    }
}
