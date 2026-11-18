import hashlib
import importlib
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from core.aggregator_core import aggregate_rankings as legacy_aggregate
from core.backends import (
    BackendUnavailableError,
    aggregate_rankings,
    backend_capabilities,
)


class _FakeNative:
    __version__ = "test-native"
    BACKEND_API_VERSION = 1
    SOURCE_FINGERPRINT_SCHEMA = 1
    SOURCE_SHA256 = "a" * 64

    def __init__(self, probabilities=None):
        self.probabilities = probabilities
        self.calls = []

    def aggregate_rankings(self, ballots, candidates, selector):
        self.calls.append((ballots, candidates, selector))
        probabilities = self.probabilities or [1.0] + [0.0] * (candidates - 1)
        return {
            "probabilities": probabilities,
            "selection": "test",
            "face": {"nonunique": False},
        }


class BackendFacadeTests(unittest.TestCase):
    def test_python_backend_matches_the_legacy_default(self):
        ballots = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]
        legacy = legacy_aggregate(ballots)
        result = aggregate_rankings(ballots, backend="python", selector="lp")

        np.testing.assert_allclose(result["probabilities"], legacy, atol=1e-12)
        self.assertEqual(result["metadata"]["backend_used"], "python")
        self.assertIsNone(result["metadata"]["fallback_reason"])

    def test_auto_keeps_python_and_does_not_load_native(self):
        ballots = [(0, 1), (1, 0), (0, 1)]
        with patch("core.backends._native", side_effect=AssertionError("must not load")):
            result = aggregate_rankings(ballots, backend="auto")

        np.testing.assert_allclose(
            result["probabilities"], legacy_aggregate(ballots), atol=1e-12
        )
        self.assertEqual(result["metadata"]["backend_used"], "python")
        self.assertIn("disabled", result["metadata"]["fallback_reason"])
        self.assertFalse(backend_capabilities()["aggregate_rankings"]["auto"]["enabled"])

    def test_rust_backend_preserves_first_ballot_candidate_order(self):
        native = _FakeNative([0.25, 0.75, 0.0])
        ballots = [("z", "x", "y"), ("x", "y", "z")]
        with patch("core.backends._native", return_value=native):
            result = aggregate_rankings(
                ballots, backend="rust", selector="minimum_norm"
            )

        self.assertEqual(result["candidates"], ["z", "x", "y"])
        self.assertEqual(native.calls, [([[0, 1, 2], [1, 2, 0]], 3, "minimum_norm")])
        self.assertEqual(result["probabilities"], [0.25, 0.75, 0.0])
        self.assertEqual(result["metadata"]["backend_used"], "rust")
        self.assertEqual(result["metadata"]["native_version"], "test-native")
        self.assertEqual(result["native_details"]["selection"], "test")

    def test_rust_rejects_python_selector_before_loading_native(self):
        with patch("core.backends._native", side_effect=AssertionError("must not load")):
            with self.assertRaisesRegex(BackendUnavailableError, "explicitly"):
                aggregate_rankings([(0, 1), (1, 0)], backend="rust")

    @unittest.skipUnless(
        importlib.util.find_spec("gtiv_native"), "optional native extension is not installed"
    )
    def test_installed_native_extension_runs_through_public_facade(self):
        native_module = importlib.import_module("gtiv_native")
        native_extension = getattr(native_module, "gtiv_native", native_module)
        extension_path = Path(native_extension.__file__)
        expected_binary_sha256 = hashlib.sha256(
            extension_path.read_bytes()
        ).hexdigest()
        result = aggregate_rankings(
            [(11, 7), (11, 7), (7, 11)],
            backend="rust",
            selector="minimum_norm",
        )

        self.assertEqual(result["candidates"], [11, 7])
        np.testing.assert_allclose(result["probabilities"], [1.0, 0.0], atol=1e-12)
        self.assertEqual(result["metadata"]["backend_used"], "rust")
        self.assertEqual(result["metadata"]["native_api_version"], 1)
        self.assertEqual(
            result["metadata"]["native_binary_sha256"], expected_binary_sha256
        )

    def test_incomplete_and_duplicate_rankings_are_rejected(self):
        for ballots in (
            [(0, 1), (1, 2)],
            [(0, 0)],
            [],
        ):
            with self.subTest(ballots=ballots):
                with self.assertRaises(ValueError):
                    aggregate_rankings(ballots)

class IterativeVotingBackendTests(unittest.TestCase):
    def test_sampled_simulator_passes_explicit_backend_through_facade(self):
        from core.voting_system import IterativeVotingSystem

        native = _FakeNative([1.0, 0.0, 0.0])
        system = IterativeVotingSystem(
            m=3,
            n=2,
            alpha=0.1,
            eta=0.1,
            beta=1.0,
            baselines=[0, 0],
            rng=np.random.default_rng(7),
            aggregation_backend="rust",
            aggregation_selector="vertex",
        )
        with patch("core.backends._native", return_value=native):
            result = system.step()

        np.testing.assert_allclose(result, [1.0, 0.0, 0.0])
        self.assertEqual(len(native.calls), 1)
        ballots, candidate_count, selector = native.calls[0]
        self.assertEqual(candidate_count, 3)
        self.assertEqual(selector, "vertex")
        self.assertEqual(len(ballots), 2)

    def test_expected_score_rejects_explicit_rust_at_construction(self):
        from core.voting_system import IterativeVotingSystem

        with self.assertRaisesRegex(BackendUnavailableError, "sampled rankings"):
            IterativeVotingSystem(
                m=3,
                n=2,
                alpha=0.1,
                eta=0.1,
                beta=1.0,
                use_expected_score=True,
                aggregation_backend="rust",
                aggregation_selector="vertex",
            )


if __name__ == "__main__":
    unittest.main()
