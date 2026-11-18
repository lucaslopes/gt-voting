"""Replay public sampled-report updates through Python and Rust.

Run from outside the source checkout with the frozen Python wheel installed:

    python current_source_replay_validation.py <installed-gtiv-cli>

The baseline distribution is one-hot and ``anchor_strength=1`` so identical
RNG streams yield identical sampled rankings and Python-owned next-state
updates even on non-unique faces. Lottery equality is required on unique
faces; on non-unique faces each backend is checked against the same independent
margin-matrix feasibility conditions, without equating selector choices.
The noncanonical first-ballot fixture also checks the simulator's numeric
candidate coordinates against the independent margin-matrix oracle.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import subprocess
from pathlib import Path

import numpy as np

import core.backends as backends
import strategies.GTStrategy as gt_strategy_module
from core.rankings_core import generate_rankings
from core.strategic_reports import generate_strategic_reports
from strategies.GTStrategy import GTStrategy


CASES = (
    ("m2_nonunique_tie", 2, ((0, 1), (1, 0)), True),
    ("m3_unique_cycle", 3, ((0, 1, 2), (1, 2, 0), (2, 0, 1)), False),
    ("m4_nonunique_tie", 4, ((0, 1, 2, 3), (3, 2, 1, 0)), True),
    (
        "m5_unique_odd",
        5,
        ((0, 1, 2, 3, 4), (1, 2, 3, 4, 0), (2, 3, 4, 0, 1)),
        False,
    ),
    ("m8_nonunique_tie", 8, (tuple(range(8)), tuple(reversed(range(8)))), True),
    ("m2_unique_noncanonical_order", 2, ((1, 0), (1, 0)), False),
)
SEED_BASE = 20261118
TIME_STEPS = 3


def margins_for(profile, m):
    margins = [[0] * m for _ in range(m)]
    for ballot in profile:
        for position, winner in enumerate(ballot):
            for loser in ballot[position + 1 :]:
                margins[winner][loser] += 1
                margins[loser][winner] -= 1
    return np.asarray(margins, dtype=np.int64)


def assert_feasible(probabilities, margins, label):
    p = np.asarray(probabilities, dtype=np.float64)
    if p.shape != (len(margins),) or not np.isfinite(p).all():
        raise AssertionError((label, "invalid probability shape or non-finite output", p))
    if np.min(p) < -1e-10 or abs(float(p.sum()) - 1.0) > 1e-10:
        raise AssertionError((label, "invalid lottery", p))
    if np.min(margins.T @ p) < -1e-8:
        raise AssertionError((label, "violates the independent GT inequalities", p, margins))


def numeric_coordinates(probabilities, candidates):
    ordered = np.zeros(len(candidates))
    ordered[np.asarray(candidates)] = probabilities
    return ordered.tolist()


def run_api(profile, m, seed, backend, selector="lp"):
    captures = {"sampled_profiles": [], "outcomes": [], "native_details": [], "state_updates": []}
    py_aggregate = gt_strategy_module.aggregate_rankings
    rust_aggregate = backends.aggregate_rankings
    strategy_update = GTStrategy._update_strategy_distribution

    def record_python(ballots, mechanism="GT"):
        captures["sampled_profiles"].append(tuple(tuple(row) for row in ballots))
        probabilities = py_aggregate(ballots, mechanism=mechanism)
        captures["outcomes"].append(numeric_coordinates(probabilities, ballots[0]))
        return probabilities

    def record_rust(ballots, mechanism="GT", **kwargs):
        captures["sampled_profiles"].append(tuple(tuple(row) for row in ballots))
        result = rust_aggregate(ballots, mechanism=mechanism, **kwargs)
        captures["outcomes"].append(
            numeric_coordinates(result["probabilities"], result["candidates"])
        )
        captures["native_details"].append(result["native_details"])
        return result

    def record_state(self, *args, **kwargs):
        updated = strategy_update(self, *args, **kwargs)
        captures["state_updates"].append(updated.copy())
        return updated

    rng = np.random.default_rng(seed)
    with (
        __import__("unittest.mock").mock.patch.object(
            gt_strategy_module, "aggregate_rankings", record_python
        ),
        __import__("unittest.mock").mock.patch.object(
            backends, "aggregate_rankings", record_rust
        ),
        __import__("unittest.mock").mock.patch.object(
            GTStrategy, "_update_strategy_distribution", record_state
        ),
    ):
        result = generate_strategic_reports(
            honest_reports=list(profile),
            T=TIME_STEPS,
            m=m,
            rng=rng,
            anchor_strength=1.0,
            learning_rate=0.2,
            sharpness=3.0,
            aggregation_backend=backend,
            aggregation_selector=selector,
        )
    captures["rng_state"] = rng.bit_generator.state
    return result, captures


def check_api_replays():
    summary = {"profiles": 0, "unique": 0, "nonunique": 0, "selectors": 0}
    for case_index, (name, m, profile, expected_nonunique) in enumerate(CASES):
        seed = SEED_BASE + case_index
        python_result, python_capture = run_api(profile, m, seed, "python")
        rust_results = {}
        rust_captures = {}
        for selector in ("vertex", "minimum_norm"):
            rust_results[selector], rust_captures[selector] = run_api(
                profile, m, seed, "rust", selector
            )
            summary["selectors"] += 1

        if len(python_capture["sampled_profiles"]) != TIME_STEPS:
            raise AssertionError((name, "Python did not capture all sampled profiles"))
        for selector, capture in rust_captures.items():
            if capture["sampled_profiles"] != python_capture["sampled_profiles"]:
                raise AssertionError((name, selector, "RNG replay sampled different ballots"))
            if capture["rng_state"] != python_capture["rng_state"]:
                raise AssertionError((name, selector, "RNG state diverged"))
            if not np.array_equal(rust_results[selector]["reports"], python_result["reports"]):
                raise AssertionError((name, selector, "reported agent state diverged"))
            if not np.allclose(
                rust_results[selector]["selected_probs"],
                python_result["selected_probs"],
                rtol=0,
                atol=1e-12,
            ):
                raise AssertionError((name, selector, "selected agent-state probabilities diverged"))
            if len(capture["state_updates"]) != TIME_STEPS:
                raise AssertionError((name, selector, "missing next-state captures"))
            for step, (python_state, rust_state) in enumerate(
                zip(python_capture["state_updates"], capture["state_updates"])
            ):
                if not np.allclose(python_state, rust_state, rtol=0, atol=1e-12):
                    raise AssertionError((name, selector, "Python-owned state diverged", step))
            for step, ballots in enumerate(capture["sampled_profiles"]):
                assert_feasible(capture["outcomes"][step], margins_for(ballots, m), (name, selector, step))
                native_details = capture["native_details"][step]
                if native_details["face"]["nonunique"] != expected_nonunique:
                    raise AssertionError((name, selector, "unexpected face classification", native_details))
                actual = rust_results[selector]["p_history"][step].tolist()
                if capture["outcomes"][step] != actual:
                    raise AssertionError((name, selector, "canonical lottery differs from trajectory"))

        for step, ballots in enumerate(python_capture["sampled_profiles"]):
            oracle = margins_for(ballots, m)
            actual = python_result["p_history"][step].tolist()
            assert_feasible(actual, oracle, (name, "python", step))
            if python_capture["outcomes"][step] != actual:
                raise AssertionError((name, "python", "canonical lottery differs from trajectory"))

        if not expected_nonunique:
            for selector in ("vertex", "minimum_norm"):
                np.testing.assert_allclose(
                    rust_results[selector]["p_history"],
                    python_result["p_history"],
                    rtol=0,
                    atol=1e-9,
                    err_msg=f"{name}: unique-face Python/Rust outcomes differ for {selector}",
                )
            summary["unique"] += 1
        else:
            summary["nonunique"] += 1
        summary["profiles"] += 1

    return summary


def check_cli_api_replay(cli_path: Path):
    name, m, profile, _ = CASES[-1]
    seed = SEED_BASE + 50
    api, _ = run_api(profile, m, seed, "rust", "minimum_norm")
    rankings = generate_rankings(m, alphabetical=False)
    baseline_indices = [rankings.index(tuple(ballot)) for ballot in profile]
    baseline_text = ",".join(map(str, baseline_indices))
    env = os.environ.copy()
    completed = subprocess.run(
        [
            str(cli_path),
            "strategic-reports",
            "--m",
            str(m),
            "--baselines",
            baseline_text,
            "--T",
            str(TIME_STEPS + 1),
            "--seed",
            str(seed),
            "--anchor-strength",
            "1.0",
            "--aggregation-backend",
            "rust",
            "--aggregation-selector",
            "minimum_norm",
            "--force-recompute",
        ],
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    if "Aggregation backend: rust (requested rust)" not in completed.stdout:
        raise AssertionError((name, "CLI did not report the selected native backend", completed.stdout))
    match = re.search(r"\[cache\] strategic_reports miss: (.+)", completed.stdout)
    if not match:
        raise AssertionError((name, "CLI did not report its cache path", completed.stdout))
    cache_dir = Path(match.group(1).strip())
    data_path = cache_dir / "data.pkl"
    if not data_path.is_file():
        raise AssertionError((name, "CLI cache artifact was not written", data_path))
    with data_path.open("rb") as stream:
        cached = pickle.load(stream)
    cli_result = cached["results"]
    if cli_result["aggregation_metadata"]["backend_used"] != "rust":
        raise AssertionError((name, "cached CLI metadata does not identify Rust"))
    np.testing.assert_allclose(cli_result["p_history"], api["p_history"], rtol=0, atol=1e-12)
    np.testing.assert_array_equal(cli_result["reports"], api["reports"])
    np.testing.assert_allclose(cli_result["selected_probs"], api["selected_probs"], rtol=0, atol=1e-12)
    if "backend-rust" not in cache_dir.name or "selector-minimum_norm" not in cache_dir.name:
        raise AssertionError((name, "cache path does not distinguish backend and selector", cache_dir))
    return {"cache_dir": str(cache_dir), "cli_backend": "rust", "api_matches_cli": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("installed_gtiv_cli", type=Path)
    args = parser.parse_args()
    report = {
        "seed_base": SEED_BASE,
        "time_steps": TIME_STEPS,
        "anchor_strength": 1.0,
        "api_replay": check_api_replays(),
        "cli_api_replay": check_cli_api_replay(args.installed_gtiv_cli.resolve()),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
