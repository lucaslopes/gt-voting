import argparse
import numpy as np
from core.honest_reports import generate_honest_reports, parse_baselines, format_rankings_readable
from core.rankings_core import generate_rankings, candidate_labels
from core.strategic_reports import generate_strategic_reports
from core.graph_utils import parse_edge_list
from plots.plot_voter_strategies import plot_voter_strategies
import matplotlib.pyplot as plt


def generate_pdf_filename(args):
    """
    Generate a descriptive PDF filename based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        str: Filename for the PDF file
    """
    parts = ["strategic_reports"]
    parts.append(f"m{args.m}")
    parts.append(f"T{args.T}")
    # Include strategy parameters
    parts.append(f"lr{args.learning_rate:.1f}")
    parts.append(f"sh{args.sharpness:.1f}")
    parts.append(f"as{args.anchor_strength:.1f}")
    parts.append(args.strategy)
    
    return "_".join(parts) + ".pdf"


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Generate strategic reports that evolve over T iterations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with GTStrategy (default) - T=5 iterations
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5
  
  # GTStrategy with custom parameters
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --anchor_strength 0.2 --learning-rate 0.3 --sharpness 5.0
  
  # Using SimilarityStrategy (backward compatibility)
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --strategy similarity_strategy --anchor_strength 0.5
  
  # Using baseline string with GTStrategy
  uv run python -m cli.strategic_reports_cli --m 3 --baselines "0*5,3*5,4*5" --T 10
  
  # With alphabetical output
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --alphabetical
  
  # With plot visualization showing trajectory over T iterations
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --plot
  
  # With custom graph topology (path graph: 0-1,1-2,2-3,3-4,4-5)
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --graph "0-1,1-2,2-3,3-4,4-5"
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
        "--strategy",
        type=str,
        default="gt_strategy",
        help="Strategy to use for evolving reports (default: gt_strategy). "
             "Available: gt_strategy, similarity_strategy"
    )
    # GTStrategy parameters
    parser.add_argument(
        "--anchor-strength",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Anchoring parameter (0-1). Controls how much voters stick to baseline. "
             "Accepts --alpha as alias. Default: 0.1 for GTStrategy, 0.5 for SimilarityStrategy"
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
        help="Learning rate (0-1) for GTStrategy. Controls update speed. "
             "Accepts --eta as alias. Only used when --strategy=gt_strategy (default: 0.2)"
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
        help="Sharpness parameter (>0) for GTStrategy. Controls exploration vs exploitation. "
             "Accepts --beta as alias. Only used when --strategy=gt_strategy (default: 3.0)"
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
        help="Distance metric for SimilarityStrategy. Only used when --strategy=similarity_strategy. "
             "Available: spearman, kendall_tau (default: spearman)"
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
    parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    parser.add_argument(
        "--graph",
        type=str,
        default=None,
        help="Edge list defining social network graph. Format: '0-1,1-2,2-0' "
             "(dash-separated pairs, comma-separated edges). "
             "If not provided, uses complete graph (default: all voters connected to all others). "
             "Only used when --strategy=gt_strategy."
    )
    
    args = parser.parse_args(args)
    
    # Validate arguments
    if args.m < 1:
        parser.error("Number of candidates must be at least 1")
    
    if args.T < 1:
        parser.error("Number of iterations (--T) must be at least 1")
    
    # Handle default values based on strategy
    if args.anchor_strength is None:
        args.anchor_strength = 0.1 if args.strategy == "gt_strategy" else 0.5
    if args.learning_rate is None:
        args.learning_rate = 0.2
    if args.sharpness is None:
        args.sharpness = 3.0
    
    # Validate strategy-specific parameters
    if args.strategy == "gt_strategy":
        if not (0 <= args.anchor_strength <= 1):
            parser.error("Anchor strength parameter must be between 0 and 1")
        if not (0 <= args.learning_rate <= 1):
            parser.error("Learning rate parameter must be between 0 and 1")
        if args.sharpness <= 0:
            parser.error("Sharpness parameter must be positive")
    elif args.strategy == "similarity_strategy":
        if not (0 <= args.anchor_strength <= 1):
            parser.error("Anchor strength parameter must be between 0 and 1")
    else:
        parser.error(f"Unknown strategy: {args.strategy}. Available: gt_strategy, similarity_strategy")
    
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
    
    # Parse graph if provided
    graph = None
    if args.graph:
        if args.strategy != "gt_strategy":
            parser.error("--graph is only supported when --strategy=gt_strategy")
        try:
            graph = parse_edge_list(args.graph, n)
        except ValueError as e:
            parser.error(f"Invalid graph specification: {e}")
    
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
        results = generate_strategic_reports(
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
            distance_metric=args.distance_metric,
            # Graph topology
            graph=graph
        )
    except ValueError as e:
        parser.error(str(e))

    # Unpack standardized results dict
    strategies = results["reports"]
    selected_probs = results.get("selected_probs")
    
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
    if args.plot or args.save:
        # Plot the heatmap showing trajectory over T+1 time steps (including t=0)
        ax = plot_voter_strategies(
            strategies,
            all_rankings,
            labels=None,
            ax=None,
            show_integers=False,
            title=(f"Strategic Reports Evolution\n({n} voters, {args.m} candidates, {args.T+1} time steps)"),
            probs=selected_probs,
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
