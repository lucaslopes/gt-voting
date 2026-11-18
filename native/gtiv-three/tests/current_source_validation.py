"""Exhaustive small and seeded large exact GT checks for the frozen source.

Usage:
    python current_source_validation.py <evaluate_exact binary> [--report PATH]

The Rust executable returns reduced rational lotteries and face certificates.
This driver independently derives margins from ballot profiles, verifies
equilibrium inequalities with Python integers/Fractions, and computes face
ranges from the margin matrix (exact vertex enumeration for m <= 4; SciPy
HiGHS LPs for the seeded m = 5..8 cases). The fixture generator and tolerances
are deterministic and declared here before the validation run.
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

SEED_BASE = 20261117
SEED_COUNT = 2
VOTER_COUNTS = (1, 2, 3, 5, 8)
LP_TOLERANCE = 1e-8


def parse_ratios(text: str) -> tuple[Fraction, ...]:
    return tuple(Fraction(item) for item in text.split(","))


def ratio_strings(values) -> list[str]:
    return [f"{value.numerator}/{value.denominator}" for value in values]


def oracle_strings(values) -> list[str]:
    return [
        f"{value.numerator}/{value.denominator}"
        if isinstance(value, Fraction)
        else format(value, ".17g")
        for value in values
    ]


def profile_family(label: str) -> str:
    for suffix in ("_relabel", "_ballot_order"):
        if label.endswith(suffix):
            label = label[: -len(suffix)]
    if label.startswith("uniform_seed_"):
        return "uniform"
    return label


def margins_for(profile: tuple[tuple[int, ...], ...], m: int) -> tuple[tuple[int, ...], ...]:
    margins = [[0] * m for _ in range(m)]
    for ballot in profile:
        for position, winner in enumerate(ballot):
            for loser in ballot[position + 1 :]:
                margins[winner][loser] += 1
                margins[loser][winner] -= 1
    return tuple(tuple(row) for row in margins)


def solve_square(matrix: list[list[Fraction]], rhs: list[Fraction]):
    size = len(rhs)
    augmented = [row[:] + [value] for row, value in zip(matrix, rhs)]
    for column in range(size):
        pivot = next((row for row in range(column, size) if augmented[row][column]), None)
        if pivot is None:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                augmented[row] = [
                    left - factor * right
                    for left, right in zip(augmented[row], augmented[column])
                ]
    return tuple(augmented[row][-1] for row in range(size))


def exact_face_ranges(margins: tuple[tuple[int, ...], ...]):
    m = len(margins)
    inequalities = []
    for candidate in range(m):
        row = [0] * m
        row[candidate] = 1
        inequalities.append(row)
    inequalities.extend(
        [[margins[candidate][opponent] for candidate in range(m)] for opponent in range(m)]
    )

    vertices = set()
    for active in itertools.combinations(range(2 * m), m - 1):
        equations = [[Fraction(1)] * m]
        equations.extend([[Fraction(x) for x in inequalities[index]] for index in active])
        point = solve_square(equations, [Fraction(1)] + [Fraction(0)] * (m - 1))
        if point is not None and all(
            sum(Fraction(a) * x for a, x in zip(row, point)) >= 0
            for row in inequalities
        ):
            vertices.add(point)
    if not vertices:
        raise AssertionError(f"independent exact oracle found no feasible vertex: {margins}")
    points = tuple(vertices)
    return (
        tuple(min(point[i] for point in points) for i in range(m)),
        tuple(max(point[i] for point in points) for i in range(m)),
    )


def scipy_face_ranges(margins: tuple[tuple[int, ...], ...]):
    m = len(margins)
    matrix = np.asarray(margins, dtype=np.float64)
    a_ub = -matrix.T
    b_ub = np.zeros(m)
    a_eq = np.ones((1, m))
    b_eq = np.ones(1)
    lower, upper = [], []
    for candidate in range(m):
        objective = np.zeros(m)
        objective[candidate] = 1.0
        result_min = linprog(
            objective,
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=(0, None),
            method="highs",
        )
        result_max = linprog(
            -objective,
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=(0, None),
            method="highs",
        )
        if not result_min.success or not result_max.success:
            raise AssertionError((margins, result_min.message, result_max.message))
        lower.append(float(result_min.fun))
        upper.append(float(-result_max.fun))
    return tuple(lower), tuple(upper)


def profiles_for(m: int):
    ranks = tuple(itertools.permutations(range(m)))
    max_voters = 5 if m <= 3 else 3
    for voters in range(1, max_voters + 1):
        for profile in itertools.product(ranks, repeat=voters):
            yield "exhaustive", m, tuple(profile)


def seeded_profiles():
    for m in range(5, 9):
        for voters in VOTER_COUNTS:
            baseline = tuple(range(m))
            rotated = (1, 2, 0, *range(3, m))
            yield "repeated", m, tuple([baseline] * voters)
            yield "near_unanimous", m, tuple([baseline] * max(0, voters - 1) + [rotated])
            cycle = (baseline, rotated, (2, 0, 1, *range(3, m)))
            yield "cyclic", m, tuple(cycle[index % 3] for index in range(voters))
            if voters % 2 == 0:
                yield "tied_reverse", m, tuple(
                    (baseline, tuple(reversed(baseline)))[index % 2] for index in range(voters)
                )
            for seed_index in range(SEED_COUNT):
                seed = SEED_BASE + m * 1000 + voters * 10 + seed_index
                rng = random.Random(seed)
                profile = tuple(tuple(rng.sample(range(m), m)) for _ in range(voters))
                yield f"uniform_seed_{seed}", m, profile


def expanded_profiles():
    for case in itertools.chain(*(profiles_for(m) for m in range(1, 5))):
        yield case
    for label, m, profile in seeded_profiles():
        yield label, m, profile
        seed = SEED_BASE + m * 1000 + len(profile)
        rng = random.Random(seed)
        relabel = list(range(m))
        rng.shuffle(relabel)
        yield f"{label}_relabel", m, tuple(
            tuple(relabel[candidate] for candidate in ballot) for ballot in profile
        )
        yield f"{label}_ballot_order", m, tuple(reversed(profile))


def encode_case(m: int, profile: tuple[tuple[int, ...], ...]) -> str:
    return f"{m} " + " ".join("".join(map(str, ballot)) for ballot in profile)


def parse_result(line: str, case):
    fields = line.split("\t")
    if len(fields) != 8 or fields[0] != "OK":
        raise AssertionError((case, line))
    return {
        "vertex": parse_ratios(fields[1]),
        "minimum_norm": parse_ratios(fields[2]),
        "minimum": parse_ratios(fields[3]),
        "maximum": parse_ratios(fields[4]),
        "nonunique": fields[5] == "true",
        "vertex_selection": fields[6],
        "minimum_norm_selection": fields[7],
    }


def assert_feasible(point, margins, case, selector):
    m = len(margins)
    if len(point) != m or any(probability < 0 for probability in point):
        raise AssertionError((case, selector, point, "invalid probability shape/sign"))
    if sum(point, Fraction(0)) != 1:
        raise AssertionError((case, selector, point, "probabilities do not sum exactly to one"))
    for opponent in range(m):
        payoff = sum(point[candidate] * margins[candidate][opponent] for candidate in range(m))
        if payoff < 0:
            raise AssertionError((case, selector, point, opponent, payoff))


def validate(binary: Path, evidence_path: Path | None = None):
    cases = list(expanded_profiles())
    payload = "".join(encode_case(m, profile) + "\n" for _, m, profile in cases)
    completed = subprocess.run(
        [str(binary)], input=payload, text=True, capture_output=True, check=True
    )
    lines = completed.stdout.splitlines()
    if len(lines) != len(cases):
        raise AssertionError((len(cases), len(lines), completed.stderr))

    face_cache = {}
    records = {}
    counts = {"cases": len(cases), "exhaustive_m1_m4": 0, "seeded_m5_m8": 0,
              "unique_faces": 0, "nonunique_faces": 0, "margin_matrices": 0,
              "cases_by_m": {}, "cases_by_family": {}}
    evidence = evidence_path.open("w", encoding="utf-8") if evidence_path else None
    for case_index, (case, line) in enumerate(zip(cases, lines)):
        label, m, profile = case
        margins = margins_for(profile, m)
        result = parse_result(line, case)
        if margins not in face_cache:
            if m <= 4:
                face_cache[margins] = exact_face_ranges(margins)
            else:
                face_cache[margins] = scipy_face_ranges(margins)
        oracle_min, oracle_max = face_cache[margins]
        for selector in ("vertex", "minimum_norm"):
            assert_feasible(result[selector], margins, case, selector)
            if any(
                result[selector][i] < result["minimum"][i]
                or result[selector][i] > result["maximum"][i]
                for i in range(m)
            ):
                raise AssertionError((case, selector, result))
        if len(result["minimum"]) != m:
            raise AssertionError((case, "invalid face minimum", result))
        if len(result["maximum"]) != m:
            raise AssertionError((case, "invalid face maximum", result))
        if any(result["minimum"][i] > result["maximum"][i] for i in range(m)):
            raise AssertionError((case, "face bounds are reversed", result))
        if m <= 4:
            unique = all(oracle_min[i] == oracle_max[i] for i in range(m))
        else:
            unique = all(abs(oracle_min[i] - oracle_max[i]) <= LP_TOLERANCE for i in range(m))
        if result["nonunique"] == unique:
            raise AssertionError((case, "Rust face uniqueness flag disagrees", result))
        for i in range(m):
            if m <= 4:
                expected_min, expected_max = oracle_min[i], oracle_max[i]
            else:
                expected_min, expected_max = Fraction(str(oracle_min[i])), Fraction(str(oracle_max[i]))
            if abs(float(result["minimum"][i]) - float(expected_min)) > LP_TOLERANCE:
                raise AssertionError((case, "face minimum differs from oracle", i, result, oracle_min))
            if abs(float(result["maximum"][i]) - float(expected_max)) > LP_TOLERANCE:
                raise AssertionError((case, "face maximum differs from oracle", i, result, oracle_max))
        if unique and result["vertex"] != result["minimum_norm"]:
            raise AssertionError((case, "selectors differ on a unique face", result))
        if label == "exhaustive":
            counts["exhaustive_m1_m4"] += 1
        else:
            counts["seeded_m5_m8"] += 1
        counts["unique_faces" if unique else "nonunique_faces"] += 1
        counts["cases_by_m"][str(m)] = counts["cases_by_m"].get(str(m), 0) + 1
        family = profile_family(label)
        counts["cases_by_family"][family] = counts["cases_by_family"].get(family, 0) + 1
        records[(m, profile)] = result
        if evidence:
            row = {
                "case_id": f"{label}-m{m}-n{len(profile)}-i{case_index:06d}",
                "family": family,
                "candidate_count": m,
                "voter_count": len(profile),
                "profile": [list(ballot) for ballot in profile],
                "margins": [list(row) for row in margins],
                "oracle": "exact_fraction_vertex_enumeration" if m <= 4 else "scipy_highs",
                "oracle_face_minimum": oracle_strings(oracle_min),
                "oracle_face_maximum": oracle_strings(oracle_max),
                "face_unique": unique,
                "backend": "rust",
                "selectors": {
                    "vertex": ratio_strings(result["vertex"]),
                    "minimum_norm": ratio_strings(result["minimum_norm"]),
                },
                "rust_face_minimum": ratio_strings(result["minimum"]),
                "rust_face_maximum": ratio_strings(result["maximum"]),
                "rust_face_nonunique": result["nonunique"],
                "selection": {
                    "vertex": result["vertex_selection"],
                    "minimum_norm": result["minimum_norm_selection"],
                },
                "status": "pass",
            }
            evidence.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    # Every seeded candidate relabeling and ballot-order permutation has a
    # corresponding base profile; compare selector behavior under the
    # documented neutrality contract and exact margin invariance.
    for label, m, profile in cases:
        if label.endswith("_ballot_order"):
            base = records[(m, tuple(reversed(profile)))]
            current = records[(m, profile)]
            if base != current:
                raise AssertionError((label, "ballot order changed outcome", base, current))
        if label.endswith("_relabel"):
            base_label = label.removesuffix("_relabel")
            # The label and profile are found by the seeded generator order.
            # Rebuild the deterministic relabel mapping from the profile's
            # size and verify minimum-norm neutrality and transformed bounds.
            rng = random.Random(SEED_BASE + m * 1000 + len(profile))
            permutation = list(range(m))
            rng.shuffle(permutation)
            original = tuple(
                tuple(permutation.index(candidate) for candidate in ballot)
                for ballot in profile
            )
            # Retrieve base via the inverse transform, independent of its label.
            original_result = records.get((m, original))
            relabeled_result = records[(m, profile)]
            if original_result is not None:
                for candidate in range(m):
                    mapped = permutation[candidate]
                    if relabeled_result["minimum_norm"][mapped] != original_result["minimum_norm"][candidate]:
                        raise AssertionError((base_label, "minimum-norm relabeling", candidate))
                    if relabeled_result["minimum"][mapped] != original_result["minimum"][candidate]:
                        raise AssertionError((base_label, "face minimum relabeling", candidate))
                    if relabeled_result["maximum"][mapped] != original_result["maximum"][candidate]:
                        raise AssertionError((base_label, "face maximum relabeling", candidate))
                if not relabeled_result["nonunique"]:
                    for candidate in range(m):
                        mapped = permutation[candidate]
                        if relabeled_result["vertex"][mapped] != original_result["vertex"][candidate]:
                            raise AssertionError((base_label, "unique vertex relabeling", candidate))

    counts["margin_matrices"] = len(face_cache)
    if evidence:
        evidence.close()
    return {
        "counts": counts,
        "seeds": {
            "base": SEED_BASE,
            "per_seed_count": SEED_COUNT,
            "uniform_formula": "base + m*1000 + voters*10 + seed_index",
            "relabel_formula": "base + m*1000 + voters",
        },
        "voter_counts_m5_m8": list(VOTER_COUNTS),
        "lp_tolerance": LP_TOLERANCE,
        "oracle": "exact Fraction vertices for m<=4; SciPy HiGHS for m=5..8",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    report = validate(
        args.binary.resolve(), args.evidence.resolve() if args.evidence else None
    )
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
