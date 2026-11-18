"""Smoke checks for a built gtiv_native wheel; uses only the standard library."""
import math

import gtiv_native


assert gtiv_native.BACKEND_API_VERSION == 1
assert gtiv_native.__version__ == "0.1.0"
assert len(gtiv_native.SOURCE_SHA256) == 64

cycle = gtiv_native.aggregate_rankings(
    [[0, 1, 2], [1, 2, 0], [2, 0, 1]], 3, selector="minimum_norm"
)
assert all(math.isclose(value, 1 / 3, abs_tol=1e-12) for value in cycle["probabilities"])
assert cycle["selection"] == "simplex_vertex"  # The optimal face is unique.
assert cycle["face"]["nonunique"] is False
assert len(cycle["exact"]) == 3

winner = gtiv_native.aggregate_rankings([[0, 1], [0, 1], [1, 0]], 2)
assert winner["probabilities"] == [1.0, 0.0]
assert winner["selection"] == "weak_condorcet_winner"
assert winner["weak_condorcet_winner"] == 0

try:
    gtiv_native.aggregate_rankings([[0, 0]], 2)
except ValueError:
    pass
else:
    raise AssertionError("invalid complete rankings must raise ValueError")

try:
    gtiv_native.aggregate_rankings([[0, 1]], 2, selector="lp")
except ValueError:
    pass
else:
    raise AssertionError("unsupported selectors must raise ValueError")
