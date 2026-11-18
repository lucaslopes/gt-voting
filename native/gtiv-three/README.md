# gtiv Rust aggregation engine

This crate contains the Rust implementation used by the optional native
backend. It is an internal path dependency; the Python package and CLI remain
the user-facing interface.

## Aggregation

`aggregate_rankings` accepts complete, unweighted rankings of 1–8 candidate
IDs. It computes the pairwise-margin game and solves its GT optimal face with
checked exact `i128` arithmetic. The result includes the lottery in candidate
ID order and a face certificate. Arithmetic overflow is returned as an error.
`Selector::Vertex` selects a feasible vertex; `Selector::MinimumNorm` selects
the minimum-Euclidean-norm point on a non-unique face. These selectors can
produce different valid lotteries when the optimal face is not unique.

This crate implements aggregation. The Python layer handles simulations and
voter report updates.

## Validation

Run the Rust tests and build the examples with:

```sh
cargo test --locked --manifest-path native/gtiv-three/Cargo.toml
cargo build --locked --examples --manifest-path native/gtiv-three/Cargo.toml
```

## License

This crate is licensed under GPL-3.0-or-later; see `LICENSE` in this
directory.
