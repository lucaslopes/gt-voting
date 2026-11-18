//! Read one profile per stdin line: `m ballot ballot ...`, each ballot a
//! string of candidate digits (e.g. `4 0123 3210 1302`). Print one line per
//! profile: `probabilities | face_min | face_max | nonunique | selection`,
//! all in candidate-ID order, or `error: ...`.
use gtiv_three::{aggregate_rankings, Selection};
use std::io::{self, BufRead, Write};

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.expect("stdin");
        let mut fields = line.split_whitespace();
        let Some(m) = fields.next().and_then(|x| x.parse::<usize>().ok()) else {
            writeln!(out, "error: missing candidate count").unwrap();
            continue;
        };
        let ballots: Option<Vec<Vec<usize>>> = fields
            .map(|b| {
                b.chars()
                    .map(|c| c.to_digit(10).map(|d| d as usize))
                    .collect()
            })
            .collect();
        let Some(ballots) = ballots else {
            writeln!(out, "error: ballots must be digit strings").unwrap();
            continue;
        };
        match aggregate_rankings(&ballots, m) {
            Ok(o) => {
                let f = |v: &[f64]| {
                    v.iter()
                        .map(|x| format!("{x:.17}"))
                        .collect::<Vec<_>>()
                        .join(" ")
                };
                let min: Vec<f64> = o.face.min.iter().map(|r| r.to_f64()).collect();
                let max: Vec<f64> = o.face.max.iter().map(|r| r.to_f64()).collect();
                let sel = match o.selection {
                    Selection::WeakCondorcetWinner(w) => format!("weak_condorcet_winner:{w}"),
                    Selection::SimplexVertex => "simplex_vertex".into(),
                    Selection::MinimumNorm => "minimum_norm".into(),
                };
                writeln!(
                    out,
                    "{} | {} | {} | {} | {}",
                    f(&o.probabilities),
                    f(&min),
                    f(&max),
                    o.face.nonunique,
                    sel
                )
                .unwrap();
            }
            Err(e) => writeln!(out, "error: {e}").unwrap(),
        }
    }
}
