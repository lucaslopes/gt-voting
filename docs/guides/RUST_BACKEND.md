# Optional Rust aggregation backend

The supported Python entry point is `gtiv.aggregate_rankings`. It keeps
the existing Python/SciPy implementation as the default and can call the
optional `gtiv_native` PyO3 extension in-process when Rust is selected
explicitly. The extension does not launch a subprocess and does not replace the
Python simulation or report-update logic.

## Install

The Python distribution remains usable without the native extension. To build
the optional extension from this checkout, install Rust and `maturin`, then run:

```sh
maturin build --release --locked --manifest-path native/gtiv-native/Cargo.toml --out dist
python -m pip install --no-deps dist/gtiv_native-*.whl
```

The `gtiv-native` package name and release availability must be checked against
the package index before any publication. This repository's native build
workflow checks wheels and a source distribution on Linux, macOS, and Windows;
that workflow is evidence only after it has run for the exact source revision.

## Python API

```python
from gtiv import aggregate_rankings, backend_capabilities

ballots = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]

# Existing behavior: Python with SciPy/HiGHS.
python_result = aggregate_rankings(ballots)

# Explicit native call; the selector is part of the requested result semantics.
rust_result = aggregate_rankings(
    ballots,
    backend="rust",
    selector="minimum_norm",
)

capabilities = backend_capabilities()
```

The facade returns candidate labels in the order of the first ballot,
probabilities in that same order, native solver details when Rust ran, and a
metadata object describing the requested and used backend, selector, package
and runtime versions, and native binary/source fingerprints. Complete rankings
must contain the same hashable candidates exactly once. The Rust implementation
accepts unweighted rankings of at most eight candidates and currently implements
the `GT` mechanism only.

`selector="vertex"` selects an optimal-face vertex. `selector="minimum_norm"`
selects the minimum-norm point on that face. They agree when the optimal face is
unique and may differ on non-unique faces; the selector is therefore explicit
for native calls. Candidate IDs for `vertex` follow the first ballot, so changing
which ballot comes first can select another vertex on a nonunique face. Use
`minimum_norm` when the selected point should be invariant to that change.
Python's `selector="lp"` keeps its SciPy/HiGHS behavior.

`backend="auto"` currently uses Python and records why native dispatch was not
selected. It will remain conservative until broad differential parity and
performance validation against this public `main` implementation is complete.

## Iterative simulation

The existing report-generation API can opt in to Rust aggregation for sampled
GT dynamics while Python continues to sample rankings and update agent
strategies:

```python
from gtiv import generate_strategic_reports

result = generate_strategic_reports(
    honest_reports=[(0, 1, 2), (1, 2, 0)],
    T=20,
    m=3,
    seed=7,
    aggregation_backend="rust",
    aggregation_selector="minimum_norm",
)
reports = result["reports"]
outcomes = result["p_history"]
provenance = result["aggregation_metadata"]
```

The columns of `p_history` and `p_avg_history` always follow numeric candidate
IDs (`0` through `m - 1`), even if the first sampled ballot orders them
differently. We apply the same order before calculating payoffs and updating
reports. This corrects older simulations that could associate a probability
with the wrong candidate. The CLI recomputes affected cached trajectories.

The `strategic-reports` CLI exposes the same opt-in path:

```sh
gtiv strategic-reports \
  --m 3 --n 15 --T 20 --seed 7 \
  --aggregation-backend rust \
  --aggregation-selector minimum_norm
```

Nondefault backend and selector requests are part of this command's cache
identity, and the output reports which backend ran. This avoids serving a
Python result for a Rust request (or the reverse) while preserving the existing
Python-default cache identity.

An explicit Rust run checks that the extension loads before reading the cache.
The compiled binary's SHA-256 is part of the cache key. A binary that cannot be
fingerprinted can still run, with caching disabled for that run.

Set `GTIV_CACHE_DIR` to choose where CLI commands store their caches. A source
checkout defaults to its `data/` directory. Installed packages use the current
user's cache directory, so CLI commands also work when Python packages are
installed read-only for multiple users.

The lower-level `IterativeVotingSystem` class also accepts the options when a
caller drives the loop one step at a time:

```python
from gtiv import IterativeVotingSystem

simulation = IterativeVotingSystem(
    m=3,
    n=15,
    alpha=0.1,
    eta=0.2,
    beta=3.0,
    aggregation_backend="rust",
    aggregation_selector="vertex",
)
outcome = simulation.step()
```

`use_expected_score=True` remains on the Python solver and cannot be combined
with an explicit Rust backend. Non-GT mechanisms and profiles above the native
candidate limit also cannot be sent to Rust. A native solver may choose a
different lottery from SciPy/HiGHS on a non-unique optimal face, so trajectories
can diverge after an explicit native call even though Python still owns the
sampling and update steps.

## CLI

The `aggregate` subcommand accepts one complete integer-ID ballot per
`--ballot` flag and emits JSON including backend metadata:

```sh
gtiv aggregate \
  --ballot 0,1,2 \
  --ballot 1,2,0 \
  --ballot 2,0,1 \
  --backend rust \
  --selector minimum_norm
```

Use `--backend python` for the default solver. `--backend auto` reports that
Python was used. The CLI's comma-separated ballot format uses integer candidate
IDs; the Python API also accepts other hashable candidate labels.
