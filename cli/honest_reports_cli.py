import argparse
from core.honest_reports import generate_honest_reports, parse_baselines, format_rankings_readable
from core.rankings_core import generate_rankings, candidate_labels
from plots.plot_voter_strategies import plot_voter_strategies
from plots.BasePlot import BasePlot
import matplotlib.pyplot as plt
import numpy as np


def generate_pdf_filename(args, n):
    """
    Generate a descriptive PDF filename based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        n: Number of voters
        
    Returns:
        str: Filename for the PDF file
    """
    parts = ["honest_reports"]
    parts.append(f"m{args.m}")
    parts.append(f"n{n}")
    if args.seed != 0:
        parts.append(f"seed{args.seed}")
    
    return "_".join(parts) + ".pdf"


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Generate honest reports from baselines or seed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using seed (default: n=15, m=3, seed=0)
  uv run python -m cli.honest_reports_cli --n 15 --m 3 --seed 42
  
  # Using baseline string (old syntax: comma-separated)
  uv run python -m cli.honest_reports_cli --n 6 --m 3 --baselines "0,1,2,0,1,2"
  
  # Using baseline string (new syntax: repetition, n inferred)
  uv run python -m cli.honest_reports_cli --m 3 --baselines "0*5,3*5,4*5"
  
  # With alphabetical output
  uv run python -m cli.honest_reports_cli --m 3 --baselines "0*5,3*5,4*5" --alphabetical
  
  # With plot visualization
  uv run python -m cli.honest_reports_cli --m 3 --baselines "0*5,3*5,4*5" --plot
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
        "--alphabetical",
        action="store_true",
        help="Output rankings in alphabetical format (default: integer format)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual heatmap of voter strategies (in addition to terminal output)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    args = parser.parse_args(args)
    
    # Validate that m is provided and positive
    if args.m < 1:
        parser.error("Number of candidates must be at least 1")
    
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
    
    # Format and output results
    if args.alphabetical:
        # Convert to alphabetical format
        labels = candidate_labels(args.m)
        for ranking in honest_reports:
            alphabetical_ranking = tuple(labels[c] for c in ranking)
            print(alphabetical_ranking)
    else:
        # Output as integer tuples
        for ranking in honest_reports:
            print(ranking)
    
    # Plot if requested
    if args.plot or args.save:
        # Get all possible rankings to find indices
        all_rankings = generate_rankings(args.m, alphabetical=False)
        
        # Convert honest reports to ranking indices
        # Create a mapping from ranking tuple to index
        ranking_to_index = {ranking: idx for idx, ranking in enumerate(all_rankings)}
        
        # Create strategies array: [n_voters, 1] where each cell is the ranking index
        strategies = np.zeros((n, 1), dtype=int)
        for i, report in enumerate(honest_reports):
            strategies[i, 0] = ranking_to_index[report]

        # For honest reports, each voter reports their baseline with probability 1.0
        selected_probs = np.ones_like(strategies, dtype=float)
        
        # Plot the heatmap
        # Always use alphabetical labels in plot for readability (show_integers=False)
        ax = plot_voter_strategies(
            strategies,
            all_rankings,
            labels=None,
            ax=None,
            show_integers=False,
            title=f"Honest Reports ({n} voters, {args.m} candidates)",
            probs=selected_probs,
        )
        
        # Save as PDF if requested
        if args.save:
            filename = generate_pdf_filename(args, n)
            plotter = BasePlot()
            fig = ax.figure
            filepath = plotter.save_figure(fig, filename)
            print(f"Plot saved to: {filepath}")
        
        # Show plot if requested
        if args.plot:
            plt.show()


if __name__ == "__main__":
    main()
