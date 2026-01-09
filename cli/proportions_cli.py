"""CLI for visualizing probability distributions as proportion plots."""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from core.honest_reports import generate_honest_reports, parse_baselines
from core.rankings_core import generate_rankings, candidate_labels
from core.strategic_reports import generate_strategic_reports
from core.aggregator_core import aggregate_rankings
from plots.plot_proportions import plot_proportions
from mechanisms import list_mechanisms


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Visualize probability distributions as proportion plots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single election from rankings
  uv run python -m cli.proportions_cli --m 3 --n 6 --seed 42
  
  # Single election from baselines
  uv run python -m cli.proportions_cli --m 3 --baselines "0*5,3*5,4*5"
  
  # Strategic reports over T iterations
  uv run python -m cli.proportions_cli --m 3 --n 6 --T 5 --anchor 0.5
  
  # Strategic reports with custom mechanism
  uv run python -m cli.proportions_cli --m 3 --n 6 --T 10 --anchor 0.7 --mechanism pairwise_majority
        """
    )
    
    # Common arguments
    parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3)"
    )
    # Get available mechanisms for help text
    available_mechanisms = list_mechanisms()
    mechanism_help = f"Aggregation mechanism (default: GT). Available: {', '.join(available_mechanisms)}"
    
    parser.add_argument(
        "--mechanism",
        type=str,
        default="GT",
        help=mechanism_help
    )
    
    # Mode selection: either single election or strategic reports
    mode_group = parser.add_mutually_exclusive_group(required=False)
    mode_group.add_argument(
        "--T",
        type=int,
        default=None,
        help="Number of iterations for strategic reports. If provided, uses strategic reports mode."
    )
    
    # Arguments for generating reports
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
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
        "--anchor",
        type=float,
        default=0.5,
        help="Anchor parameter (0-1) for strategic reports. Only used when --T is provided. "
             "1.0 = reports never change, 0.0 = reports can change completely randomly (default: 0.5)"
    )
    parser.add_argument(
        "--distance-metric",
        type=str,
        default="spearman",
        help="Distance metric for strategic reports. Only used when --T is provided. "
             "Available: spearman, kendall_tau (default: spearman)"
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom title for the plot"
    )
    parser.add_argument(
        "--show-integers",
        action="store_true",
        help="Show candidate integers instead of alphabetical labels in legend"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual proportion plot (stacked area chart)"
    )
    
    args = parser.parse_args(args)
    
    # Validate arguments
    if args.m < 1:
        parser.error("Number of candidates must be at least 1")
    
    if args.T is not None and args.T < 1:
        parser.error("Number of iterations (--T) must be at least 1")
    
    if args.T is not None and not (0 <= args.anchor <= 1):
        parser.error("Anchor parameter must be between 0 and 1")
    
    # Determine mode: strategic reports (if --T provided) or single election
    is_strategic = args.T is not None
    
    if is_strategic:
        # Strategic reports mode: generate reports over T iterations
        # Parse baselines if provided
        if args.baselines:
            try:
                baselines, inferred_n = parse_baselines(args.baselines, args.m, args.n)
            except ValueError as e:
                parser.error(str(e))
            
            n = inferred_n if args.n is None else args.n
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
        
        # Get all possible rankings
        all_rankings = generate_rankings(args.m, alphabetical=False)
        
        # Print summary
        print(f"Strategic Reports Mode:")
        print(f"  Voters: {n}")
        print(f"  Candidates: {args.m}")
        print(f"  Time steps: {args.T + 1} (t=0 to t={args.T})")
        print(f"  Anchor: {args.anchor}")
        print(f"  Mechanism: {args.mechanism}")
        print()
        
        # Print probabilities for each time step
        for t in range(args.T + 1):
            rankings_at_t = [all_rankings[strategies[i, t]] for i in range(n)]
            probs = aggregate_rankings(rankings_at_t, mechanism=args.mechanism)
            print(f"Time step t={t}: {probs}")
        
        # Plot if requested
        if args.plot:
            plot_proportions(
                strategies,
                m=args.m,
                all_rankings=all_rankings,
                labels=None,
                mechanism=args.mechanism,
                ax=None,
                title=args.title,
                show_integers=args.show_integers
            )
            plt.show()
        
    else:
        # Single election mode: generate one set of rankings
        # Parse baselines if provided
        if args.baselines:
            try:
                baselines, inferred_n = parse_baselines(args.baselines, args.m, args.n)
            except ValueError as e:
                parser.error(str(e))
            
            n = inferred_n if args.n is None else args.n
            if args.n is not None and inferred_n != args.n:
                parser.error(f"Number of voters from --baselines ({inferred_n}) doesn't match --n ({args.n})")
        else:
            baselines = None
            n = args.n if args.n is not None else 15
        
        # Generate honest reports (single election)
        try:
            reported_rankings = generate_honest_reports(
                m=args.m,
                n=n,
                baselines=baselines,
                seed=args.seed
            )
        except ValueError as e:
            parser.error(str(e))
        
        # Aggregate to get probabilities
        try:
            probs = aggregate_rankings(reported_rankings, mechanism=args.mechanism)
        except ValueError as e:
            parser.error(str(e))
        
        # Print summary
        print(f"Single Election Mode:")
        print(f"  Voters: {n}")
        print(f"  Candidates: {args.m}")
        print(f"  Mechanism: {args.mechanism}")
        print()
        
        # Print probabilities
        labels = candidate_labels(args.m)
        print("Probability Distribution:")
        for i, prob in enumerate(probs):
            candidate_label = labels[i] if not args.show_integers else str(i)
            print(f"  Candidate {candidate_label}: {prob:.4f}")
        print()
        
        # Plot if requested
        if args.plot:
            plot_proportions(
                reported_rankings,
                m=args.m,
                all_rankings=None,
                labels=None,
                mechanism=args.mechanism,
                ax=None,
                title=args.title,
                show_integers=args.show_integers
            )
            plt.show()


if __name__ == "__main__":
    main()
