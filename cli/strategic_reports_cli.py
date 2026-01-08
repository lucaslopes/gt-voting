import argparse
import numpy as np
from core.honest_reports import generate_honest_reports, parse_baselines, format_rankings_readable
from core.rankings_core import generate_rankings, candidate_labels
from core.strategic_reports import generate_strategic_reports
from plots.plot_voter_strategies import plot_voter_strategies
import matplotlib.pyplot as plt


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Generate strategic reports that evolve over T iterations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with T=5 iterations and anchor=0.5
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --anchor 0.5
  
  # Using baseline string with T=10 iterations
  uv run python -m cli.strategic_reports_cli --m 3 --baselines "0*5,3*5,4*5" --T 10 --anchor 0.7
  
  # With different distance metric (when implemented)
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --anchor 0.5 --distance-metric spearman
  
  # With alphabetical output
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --anchor 0.5 --alphabetical
  
  # With plot visualization showing trajectory over T iterations
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --anchor 0.5 --plot
        """
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
    )
    parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3, required to validate baseline indices)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0, used when --baselines not provided)"
    )
    parser.add_argument(
        "--baselines",
        type=str,
        default=None,
        help="Baseline permutation indices. Supports two formats:\n"
             "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
             "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
             "Indices refer to positions in the sorted list from generate_rankings(m).\n"
             "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly."
    )
    parser.add_argument(
        "--T",
        type=int,
        required=True,
        help="Number of iterations (time steps) for strategic evolution"
    )
    parser.add_argument(
        "--anchor",
        type=float,
        default=0.5,
        help="Anchor parameter (0-1) controlling how closely reports stay to honest reports. "
             "1.0 = reports never change, 0.0 = reports can change completely randomly (default: 0.5)"
    )
    parser.add_argument(
        "--distance-metric",
        type=str,
        default="spearman",
        help="Distance metric to use for similarity calculation (default: spearman). "
             "Available: spearman"
    )
    parser.add_argument(
        "--alphabetical",
        action="store_true",
        help="Output rankings in alphabetical format (default: integer format)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual heatmap of voter strategy evolution over T iterations"
    )
    
    args = parser.parse_args(args)
    
    # Validate arguments
    if args.m < 1:
        parser.error("Number of candidates must be at least 1")
    
    if args.T < 1:
        parser.error("Number of iterations (--T) must be at least 1")
    
    if not (0 <= args.anchor <= 1):
        parser.error("Anchor parameter must be between 0 and 1")
    
    # Parse baselines if provided, otherwise use defaults
    if args.baselines:
        try:
            baselines, inferred_n = parse_baselines(args.baselines, args.m, args.n)
        except ValueError as e:
            parser.error(str(e))
        
        # Use inferred n if n was not explicitly provided
        n = inferred_n if args.n is None else args.n
        # Double-check they match
        if args.n is not None and inferred_n != args.n:
            parser.error(f"Number of voters from --baselines ({inferred_n}) doesn't match --n ({args.n})")
    else:
        baselines = None
        n = args.n if args.n is not None else 15
    
    # Generate honest reports
    try:
        honest_reports = generate_honest_reports(
            m=args.m,
            n=n,
            baselines=baselines,
            seed=args.seed
        )
    except ValueError as e:
        parser.error(str(e))
    
    # Generate strategic reports
    try:
        strategies = generate_strategic_reports(
            honest_reports=honest_reports,
            T=args.T,
            anchor=args.anchor,
            m=args.m,
            seed=args.seed,
            distance_metric=args.distance_metric
        )
    except ValueError as e:
        parser.error(str(e))
    
    # Get all possible rankings for output formatting
    all_rankings = generate_rankings(args.m, alphabetical=False)
    
    # Output results
    # Output format: for each voter, show their trajectory (all T+1 time steps)
    if args.alphabetical:
        labels = candidate_labels(args.m)
        for i in range(n):
            print(f"Voter {i}:")
            for t in range(args.T + 1):
                ranking_idx = strategies[i, t]
                ranking = all_rankings[ranking_idx]
                alphabetical_ranking = tuple(labels[c] for c in ranking)
                ranking_str = ">".join(alphabetical_ranking)
                print(f"  t={t}: {ranking_str}")
    else:
        for i in range(n):
            print(f"Voter {i}:")
            for t in range(args.T + 1):
                ranking_idx = strategies[i, t]
                ranking = all_rankings[ranking_idx]
                print(f"  t={t}: {ranking}")
    
    # Plot if requested
    if args.plot:
        # Plot the heatmap showing trajectory over T+1 time steps (including t=0)
        plot_voter_strategies(
            strategies,
            all_rankings,
            labels=None,
            ax=None,
            show_integers=False,
            title=f"Strategic Reports Evolution (n={n}, m={args.m}, T={args.T}, anchor={args.anchor})"
        )
        plt.show()


if __name__ == "__main__":
    main()
