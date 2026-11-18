import hashlib
import io
import importlib.util
import os
import pickle
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path
from unittest.mock import patch

import numpy as np


class _FakeNative:
    __version__ = "test-native"
    BACKEND_API_VERSION = 1
    SOURCE_FINGERPRINT_SCHEMA = 1
    SOURCE_SHA256 = "b" * 64

    def __init__(self):
        self.calls = []

    def aggregate_rankings(self, ballots, candidates, selector):
        self.calls.append((ballots, candidates, selector))
        return {
            "probabilities": [1.0] + [0.0] * (candidates - 1),
            "selection": "fake",
            "face": {"nonunique": False},
        }


class StrategicReportsBackendTests(unittest.TestCase):
    def test_python_default_and_explicit_python_report_runs_match(self):
        from core.strategic_reports import generate_strategic_reports

        arguments = {
            "honest_reports": [(0, 1, 2), (1, 2, 0)],
            "T": 2,
            "m": 3,
            "seed": 17,
        }
        default = generate_strategic_reports(**arguments)
        explicit_python = generate_strategic_reports(
            **arguments,
            aggregation_backend="python",
            aggregation_selector="lp",
        )

        for key in ("reports", "selected_probs", "p_history", "p_avg_history"):
            np.testing.assert_array_equal(default[key], explicit_python[key])
        self.assertEqual(default["payoffs_history"], explicit_python["payoffs_history"])
        self.assertNotIn("aggregation_metadata", default)
        self.assertNotIn("aggregation_metadata", explicit_python)

    @unittest.skipUnless(
        importlib.util.find_spec("gtiv_native"), "optional native extension is not installed"
    )
    def test_installed_native_backend_updates_sampled_agent_reports(self):
        from core.strategic_reports import generate_strategic_reports

        result = generate_strategic_reports(
            honest_reports=[(0, 1, 2), (0, 1, 2)],
            T=1,
            m=3,
            seed=5,
            aggregation_backend="rust",
            aggregation_selector="minimum_norm",
        )

        np.testing.assert_allclose(result["p_history"], [[1.0, 0.0, 0.0]])
        self.assertEqual(result["reports"].shape, (2, 2))
        self.assertEqual(result["aggregation_metadata"]["backend_used"], "rust")

    def test_report_generation_uses_rust_for_sampled_aggregation(self):
        from core.strategic_reports import generate_strategic_reports

        native = _FakeNative()
        with patch("core.backends._native", return_value=native):
            result = generate_strategic_reports(
                honest_reports=[(0, 1, 2), (0, 1, 2)],
                T=1,
                m=3,
                seed=5,
                aggregation_backend="rust",
                aggregation_selector="vertex",
            )

        np.testing.assert_allclose(result["p_history"], [[1.0, 0.0, 0.0]])
        self.assertEqual(len(native.calls), 1)
        ballots, candidate_count, selector = native.calls[0]
        self.assertEqual(candidate_count, 3)
        self.assertEqual(selector, "vertex")
        self.assertEqual(len(ballots), 2)
        self.assertEqual(result["aggregation_metadata"]["backend_used"], "rust")

    def test_auto_remains_python_and_reports_its_fallback(self):
        from core.strategic_reports import generate_strategic_reports

        with patch("core.backends._native", side_effect=AssertionError("must not load")):
            result = generate_strategic_reports(
                honest_reports=[(0, 1), (1, 0)],
                T=1,
                m=2,
                seed=2,
                aggregation_backend="auto",
            )

        self.assertEqual(result["aggregation_metadata"]["backend_used"], "python")
        self.assertIn("disabled", result["aggregation_metadata"]["fallback_reason"])

    def test_existing_strategic_reports_cli_routes_and_caches_backend_choice(self):
        from main import main as unified_main
        from cli import strategic_reports_cli

        native = _FakeNative()
        output = io.StringIO()
        with tempfile.TemporaryDirectory(prefix="gtiv-cli-cache-") as temp_dir:
            binary = Path(temp_dir) / f"gtiv_native{EXTENSION_SUFFIXES[0]}"
            binary.write_bytes(b"test binary")
            native.__file__ = str(binary)
            with (
                patch("core.backends._native", return_value=native),
                patch.object(
                    strategic_reports_cli,
                    "get_run_path",
                    return_value=Path(temp_dir),
                ),
                patch.object(strategic_reports_cli, "save_cached_run") as save_cache,
                patch.object(
                    sys,
                    "argv",
                    [
                        "main.py",
                        "strategic-reports",
                        "--m",
                        "3",
                        "--n",
                        "2",
                        "--baselines",
                        "0*2",
                        "--T",
                        "2",
                        "--aggregation-backend",
                        "rust",
                        "--aggregation-selector",
                        "vertex",
                        "--force-recompute",
                    ],
                ),
                redirect_stdout(output),
            ):
                unified_main()

        params = save_cache.call_args.kwargs["params"]
        self.assertEqual(params["aggregation_backend"], "rust")
        self.assertEqual(params["aggregation_selector"], "vertex")
        self.assertEqual(params["native_binary_sha256"], hashlib.sha256(b"test binary").hexdigest())
        self.assertEqual(len(native.calls), 1)
        self.assertIn("Aggregation backend: rust (requested rust)", output.getvalue())

    def test_rust_cache_requires_the_same_available_binary(self):
        from cli import strategic_reports_cli

        native = _FakeNative()
        arguments = [
            "--m", "2", "--baselines", "0*2", "--T", "2",
            "--aggregation-backend", "rust", "--aggregation-selector", "vertex",
        ]
        with tempfile.TemporaryDirectory(prefix="gtiv-rust-cache-") as temp_dir:
            directory = Path(temp_dir)
            binary = directory / f"gtiv_native{EXTENSION_SUFFIXES[0]}"
            native.__file__ = str(binary)
            binary.write_bytes(b"first binary")
            cache_dir = directory / "cache"
            with patch.dict(os.environ, {"GTIV_CACHE_DIR": str(cache_dir)}):
                with patch("core.backends._native", return_value=native):
                    with redirect_stdout(io.StringIO()) as output:
                        strategic_reports_cli.main(arguments)
                        strategic_reports_cli.main(arguments)
                    self.assertIn("[cache] strategic_reports hit:", output.getvalue())
                    self.assertEqual(len(native.calls), 1)

                    cache_files = list(cache_dir.glob("strategic_reports_runs/*/data.pkl"))
                    self.assertEqual(len(cache_files), 1)
                    with cache_files[0].open("rb") as stream:
                        payload = pickle.load(stream)
                    payload["results"]["aggregation_metadata"]["native_binary_sha256"] = "0" * 64
                    with cache_files[0].open("wb") as stream:
                        pickle.dump(payload, stream)
                    with redirect_stdout(io.StringIO()) as output:
                        strategic_reports_cli.main(arguments)
                    self.assertIn("[cache] strategic_reports miss:", output.getvalue())
                    self.assertEqual(len(native.calls), 2)

                    binary.write_bytes(b"a different binary")
                    with redirect_stdout(io.StringIO()) as output:
                        strategic_reports_cli.main(arguments)
                    self.assertIn("[cache] strategic_reports miss:", output.getvalue())
                    self.assertEqual(len(native.calls), 3)
                    self.assertEqual(len(list(cache_dir.glob("strategic_reports_runs/*/data.pkl"))), 2)

                with (
                    patch("core.backends._native", return_value=None),
                    patch.object(strategic_reports_cli, "load_cached_run") as load,
                    redirect_stderr(io.StringIO()) as output,
                    self.assertRaises(SystemExit) as raised,
                ):
                    strategic_reports_cli.main(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("gtiv_native is not installed", output.getvalue())
                load.assert_not_called()

    def test_unfingerprintable_rust_runs_without_cache(self):
        from cli import strategic_reports_cli

        native = _FakeNative()
        with (
            patch("core.backends._native", return_value=native),
            patch.object(strategic_reports_cli, "load_cached_run") as load,
            patch.object(strategic_reports_cli, "save_cached_run") as save,
            redirect_stdout(io.StringIO()) as output,
        ):
            strategic_reports_cli.main([
                "--m", "2", "--baselines", "0*2", "--T", "2",
                "--aggregation-backend", "rust", "--aggregation-selector", "vertex",
            ])
        self.assertEqual(len(native.calls), 1)
        self.assertIn("the Rust binary could not be fingerprinted", output.getvalue())
        load.assert_not_called()
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
