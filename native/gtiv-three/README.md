# gtiv Rust voting engine

The optional Python native backend uses this crate for exact aggregation.
Rust consumers can also use the assembly API by pinning a GTIV source revision.

## Aggregation

`aggregate_rankings` accepts complete, unweighted rankings of 1–8 candidate
IDs. It computes the pairwise-margin game and solves its GT optimal face with
checked exact `i128` arithmetic. The result includes the lottery in candidate
ID order and a face certificate. Arithmetic overflow is returned as an error.
`Selector::Vertex` selects a feasible vertex; `Selector::MinimumNorm` selects
the minimum-Euclidean-norm point on a non-unique face. These selectors can
produce different valid lotteries when the optimal face is not unique.

## Iterative assemblies in Rust

`Assembly` supports complete, unweighted rankings of 2–8 candidates. Each round
produces sampled reports, an exact maximal lottery and updated reporting tendencies.
Callers choose the face selector and whether the display and neighbor reports
use the current round or the baseline. `Assembly::step` consumes one uniform draw
per voter through `UniformSource`. Use `Assembly::step_with_reports` to supply
reports directly. The cubic update enumerates `m!` rankings, so large candidate
sets increase runtime and memory use.

The Python native extension continues to expose aggregation. For a Wasm
application, link this Rust crate behind the application's own interface.
Exact lottery values are rational. Floating-point tendency updates can differ
in the last bits across targets because of `exp`.

## Validation

Run the Rust tests and build the examples with:

```sh
cargo test --locked --manifest-path native/gtiv-three/Cargo.toml
cargo build --locked --examples --manifest-path native/gtiv-three/Cargo.toml
```

## License

This crate is licensed under GPL-3.0-or-later; see `LICENSE` in this
directory.
