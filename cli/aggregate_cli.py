"""Machine-readable CLI for aggregating explicit complete rankings."""

import argparse
import json

from core.backends import BackendUnavailableError, aggregate_rankings


def parse_ballot(value):
    """Parse a comma-separated ranking of integer candidate IDs."""
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(not part for part in parts):
        raise argparse.ArgumentTypeError("ballots must be comma-separated integer IDs")
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "ballots must contain only integer candidate IDs"
        ) from exc


def add_arguments(parser):
    parser.add_argument(
        "--ballot",
        action="append",
        type=parse_ballot,
        required=True,
        metavar="ID,ID,...",
        help="Complete ranking of integer candidate IDs; repeat once per voter",
    )
    parser.add_argument("--mechanism", default="GT", help="Aggregation mechanism (default: GT)")
    parser.add_argument(
        "--backend",
        choices=("python", "rust", "auto"),
        default="python",
        help="Aggregation backend (default: python; auto currently stays on Python)",
    )
    parser.add_argument(
        "--selector",
        choices=("lp", "vertex", "minimum_norm", "minimum-norm", "qp-balanced"),
        default="lp",
        help="Solver selection; Rust requires vertex or minimum_norm",
    )


def run(args):
    """Return the aggregation result as stable, indented JSON text."""
    result = aggregate_rankings(
        args.ballot,
        mechanism=args.mechanism,
        backend=args.backend,
        selector=args.selector,
    )
    return json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Aggregate complete rankings and report backend provenance"
    )
    add_arguments(parser)
    args = parser.parse_args(argv)
    try:
        output = run(args)
    except (BackendUnavailableError, ValueError) as exc:
        parser.error(str(exc))
    print(output)


if __name__ == "__main__":
    main()
