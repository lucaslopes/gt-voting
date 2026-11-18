import io
import importlib.util
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import numpy as np

from cli import proportions_cli
from core.backends import aggregate_rankings
from core.strategic_reports import generate_strategic_reports
from core.voting_system import IterativeVotingSystem


_BALLOTS = [(1, 0), (1, 0)]


class CandidateOrderTests(unittest.TestCase):
    def test_single_aggregate_preserves_first_ballot_order(self):
        result = aggregate_rankings(_BALLOTS)
        self.assertEqual(result["candidates"], [1, 0])
        self.assertEqual(result["probabilities"], [1.0, 0.0])

    def _assert_simulators_use_candidate_ids(self, backend, selector):
        report_result = generate_strategic_reports(
            _BALLOTS,
            T=2,
            m=2,
            seed=42,
            anchor_strength=0,
            learning_rate=1,
            sharpness=5,
            aggregation_backend=backend,
            aggregation_selector=selector,
        )
        np.testing.assert_array_equal(report_result["p_history"], [[0, 1], [0, 1]])
        np.testing.assert_array_equal(report_result["p_avg_history"], [[0, 1], [0, 1]])
        np.testing.assert_array_equal(report_result["reports"], np.ones((2, 3)))

        system = IterativeVotingSystem(
            m=2,
            n=2,
            alpha=0,
            eta=1,
            beta=5,
            baselines=[1, 1],
            rng=np.random.default_rng(42),
            aggregation_backend=backend,
            aggregation_selector=selector,
        )
        np.testing.assert_array_equal(system.step(), [0, 1])
        np.testing.assert_array_equal(np.argmax(system.x, axis=1), [1, 1])

    def test_python_and_auto_simulators_advance_the_correct_candidate(self):
        for backend in ("python", "auto"):
            with self.subTest(backend=backend):
                self._assert_simulators_use_candidate_ids(backend, "lp")

    @unittest.skipUnless(importlib.util.find_spec("gtiv_native"), "native extension not installed")
    def test_rust_simulators_advance_the_correct_candidate(self):
        for selector in ("vertex", "minimum_norm"):
            with self.subTest(selector=selector):
                self._assert_simulators_use_candidate_ids("rust", selector)

    def test_single_proportions_cli_uses_its_existing_cache_and_correct_candidate_labels(self):
        cache = {"n": 2, "reported_rankings": _BALLOTS, "probs": [1.0, 0.0]}
        output = io.StringIO()
        with (
            patch.object(proportions_cli, "load_cached_run", return_value=(cache, {})) as load,
            patch.object(proportions_cli, "save_cached_run") as save,
            redirect_stdout(output),
        ):
            proportions_cli.main(["--m", "2", "--n", "2", "--show-integers"])

        self.assertEqual(load.call_args.kwargs["schema_version"], 1)
        save.assert_not_called()
        self.assertIn("Candidate 0: 0.0000", output.getvalue())
        self.assertIn("Candidate 1: 1.0000", output.getvalue())
