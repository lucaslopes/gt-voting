import argparse
from core.rankings_core import generate_rankings
from plots.plot_rankings import plot_rankings_list
import matplotlib.pyplot as plt


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Generate and display all possible candidate rankings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Integer format (default)
  uv run python rankings.py --m 3
  
  # Alphabetical format
  uv run python rankings.py --m 3 --alphabetical
  
  # Using --candidates instead of --m
  uv run python rankings.py --candidates 4
  
  # With plot visualization (auto layout)
  uv run python rankings.py --m 3 --plot
  
  # With specific layout
  uv run python rankings.py --m 3 --plot --layout horizontal
  uv run python rankings.py --m 4 --plot --layout matrix
        """
    )
    parser.add_argument(
        "--m",
        type=int,
        default=None,
        help="Number of candidates (required if --candidates not provided)"
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=None,
        dest="m",
        help="Number of candidates (alternative to --m)"
    )
    parser.add_argument(
        "--alphabetical",
        action="store_true",
        help="Output rankings in alphabetical format (default: integer format)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual plot of all rankings (in addition to terminal output)"
    )
    parser.add_argument(
        "--layout",
        type=str,
        choices=['horizontal', 'vertical', 'matrix', 'auto'],
        default='auto',
        help="Layout style for the plot: 'horizontal' (single row), 'vertical' (single column), 'matrix' (grid), or 'auto' (default, chooses based on number of rankings)"
    )
    
    args = parser.parse_args(args)
    
    # Validate that m is provided
    if args.m is None:
        parser.error("Number of candidates must be provided via --m or --candidates")
    
    if args.m < 1:
        parser.error("Number of candidates must be at least 1")
    
    # Generate and print rankings
    rankings = generate_rankings(args.m, alphabetical=args.alphabetical)
    
    for ranking in rankings:
        print(ranking)
    
    # Plot if requested
    if args.plot:
        # _prepare_labels() in plot_rankings.py will handle label generation/extraction
        # Pass show_integers flag to respect the --alphabetical CLI argument
        plot_rankings_list(rankings, labels=None, layout=args.layout, show_integers=not args.alphabetical)
        plt.show()


if __name__ == "__main__":
    main()
