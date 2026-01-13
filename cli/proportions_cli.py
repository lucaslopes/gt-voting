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


def generate_pdf_filename(args):
    """
    Generate a descriptive PDF filename based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        str: Filename for the PDF file
    """
    parts = ["proportions"]
    parts.append(f"m{args.m}")
    
    if args.T is not None:
        parts.append(f"T{args.T}")
        # Include strategy parameters if T is provided
        parts.append(f"lr{args.learning_rate:.1f}")
        parts.append(f"sh{args.sharpness:.1f}")
        parts.append(f"as{args.anchor_strength:.1f}")
    
    # Add mechanism
    parts.append(args.mechanism)
    
    return "_".join(parts) + ".pdf"


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
  uv run python -m cli.proportions_cli --m 3 --n 6 --T 5 --anchor-strength 0.5
  
  # Strategic reports with custom mechanism
  uv run python -m cli.proportions_cli --m 3 --n 6 --T 10 --anchor-strength 0.7 --mechanism pairwise_majority
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
        "--strategy",
        type=str,
        default="gt_strategy",
        help="Strategy to use for evolving reports. Only used when --T is provided. "
             "Available: gt_strategy, similarity_strategy (default: gt_strategy)"
    )
    # GTStrategy parameters
    parser.add_argument(
        "--anchor-strength",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Anchoring strength parameter (0-1). Controls how much voters stick to baseline. "
             "Accepts --alpha as alias. Only used when --T is provided. "
             "Default: 0.1 for GTStrategy, 0.5 for SimilarityStrategy"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Alias for --anchor-strength (deprecated, use --anchor-strength instead)"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.2,
        dest="learning_rate",
        help="Learning rate (0-1) for GTStrategy. Accepts --eta as alias. "
             "Only used when --T is provided and --strategy=gt_strategy. "
             "Controls update speed (default: 0.2)"
    )
    parser.add_argument(
        "--eta",
        type=float,
        default=None,
        dest="learning_rate",
        help="Alias for --learning-rate (deprecated, use --learning-rate instead)"
    )
    parser.add_argument(
        "--sharpness",
        type=float,
        default=3.0,
        dest="sharpness",
        help="Sharpness parameter (>0) for GTStrategy. Accepts --beta as alias. "
             "Only used when --T is provided and --strategy=gt_strategy. "
             "Controls exploration vs exploitation (default: 3.0)"
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=None,
        dest="sharpness",
        help="Alias for --sharpness (deprecated, use --sharpness instead)"
    )
    parser.add_argument(
        "--distance-metric",
        type=str,
        default="spearman",
        help="Distance metric for SimilarityStrategy. Only used when --T is provided and --strategy=similarity_strategy. "
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
    parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    args = parser.parse_args(args)
    
    # Validate arguments
    if args.m < 1:
        parser.error("Number of candidates must be at least 1")
    
    if args.T is not None and args.T < 1:
        parser.error("Number of iterations (--T) must be at least 1")
    
    # Handle default values based on strategy
    if args.anchor_strength is None:
        args.anchor_strength = 0.1 if args.strategy == "gt_strategy" else 0.5
    if args.learning_rate is None:
        args.learning_rate = 0.2
    if args.sharpness is None:
        args.sharpness = 3.0
    
    if args.T is not None and not (0 <= args.anchor_strength <= 1):
        parser.error("Anchor strength parameter must be between 0 and 1")
    
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
            strategies_result = generate_strategic_reports(
                honest_reports=honest_reports,
                T=args.T,
                m=args.m,
                seed=args.seed,
            strategy=args.strategy,
            # GTStrategy parameters
            anchor_strength=args.anchor_strength,
            learning_rate=args.learning_rate,
            sharpness=args.sharpness,
            # SimilarityStrategy parameters
            distance_metric=args.distance_metric
            )
        except ValueError as e:
            parser.error(str(e))
        
        # Extract the reports array from the dict (generate_strategic_reports returns a dict)
        strategies = strategies_result["reports"]
        
        # Get all possible rankings
        all_rankings = generate_rankings(args.m, alphabetical=False)
        
        # Print summary
        print(f"Strategic Reports Mode:")
        print(f"  Voters: {n}")
        print(f"  Candidates: {args.m}")
        print(f"  Time steps: {args.T + 1} (t=0 to t={args.T})")
        print(f"  Strategy: {args.strategy}")
        if args.strategy == "gt_strategy":
            print(f"  Anchor strength: {args.anchor_strength}, Learning Rate: {args.learning_rate}, Sharpness: {args.sharpness}")
        else:
            print(f"  Anchor strength: {args.anchor_strength}, Distance Metric: {args.distance_metric}")
        print(f"  Mechanism: {args.mechanism}")
        print()
        
        # Print probabilities for each time step
        for t in range(args.T + 1):
            rankings_at_t = [all_rankings[strategies[i, t]] for i in range(n)]
            probs = aggregate_rankings(rankings_at_t, mechanism=args.mechanism)
            print(f"Time step t={t}: {probs}")
        
        # Plot if requested
        if args.plot or args.save:
            ax = plot_proportions(
                strategies,
                m=args.m,
                all_rankings=all_rankings,
                labels=None,
                mechanism=args.mechanism,
                ax=None,
                title=args.title,
                show_integers=args.show_integers
            )
            
            # Save as PDF if requested
            if args.save:
                filename = generate_pdf_filename(args)
                fig = ax.figure
                fig.savefig(
                    filename,
                    format='pdf',
                    dpi=300,
                    bbox_inches='tight',
                    pad_inches=0.1
                )
                print(f"Plot saved to: {filename}")
            
            # Show plot if requested
            if args.plot:
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
        if args.plot or args.save:
            ax = plot_proportions(
                reported_rankings,
                m=args.m,
                all_rankings=None,
                labels=None,
                mechanism=args.mechanism,
                ax=None,
                title=args.title,
                show_integers=args.show_integers
            )
            
            # Save as PDF if requested
            if args.save:
                filename = generate_pdf_filename(args)
                fig = ax.figure
                fig.savefig(
                    filename,
                    format='pdf',
                    dpi=300,
                    bbox_inches='tight',
                    pad_inches=0.1
                )
                print(f"Plot saved to: {filename}")
            
            # Show plot if requested
            if args.plot:
                plt.show()


if __name__ == "__main__":
    main()
