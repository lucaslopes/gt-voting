# Optional native aggregation module

`gtiv-native` provides the `gtiv_native` PyO3 extension for the Rust GT
aggregation crate. This first package version exposes one operation:
`aggregate_rankings`. It accepts complete, unweighted rankings of candidate IDs
and returns probabilities, exact rational values, margins, the selected
optimal-face point, and a face certificate.

The selector is explicit: `vertex` returns a feasible face vertex, while
`minimum_norm` selects the minimum-norm point. On non-unique faces, these
results can differ while both satisfy the GT equilibrium conditions. The
module raises `ValueError` for invalid input and `OverflowError` when checked
exact arithmetic exceeds its supported range.

## Local build

From the repository root, install Rust and `maturin`, then build and install
the wheel:

```sh
maturin build --release --locked --manifest-path native/gtiv-native/Cargo.toml --out dist
python -m pip install --no-deps dist/gtiv_native-*.whl
```

The `gtiv` distribution runs with the Python backend by default. The
`gtiv_native` module is an internal interface for the optional backend.

New builds expose `SOURCE_SHA256` and `SOURCE_FINGERPRINT_SCHEMA`. Schema 1
hashes the Rust aggregation source, binding source, build script, and
`Cargo.lock` using length-framed file names and content. The Python adapter
should report this digest alongside its own package version and requested
backend.

## License

This extension and the wrapped Rust crate are licensed under
GPL-3.0-or-later; see `LICENSE` in this directory.
