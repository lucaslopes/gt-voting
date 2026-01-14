"""CLI for visualizing phase transition experiment: distance from center vs anchoring parameter."""

import argparse
import matplotlib.pyplot as plt
from core.honest_reports import parse_baselines
from plots.plot_phase_transition import plot_phase_transition
from plots.BasePlot import BasePlot


def generate_pdf_filename(args):
    """
    Generate a descriptive PDF filename based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        str: Filename for the PDF file
    """
    parts = ["phase_transition"]
    parts.append(f"m{args.m}")
    parts.append(f"n{args.n}")
    parts.append(f"runs{args.runs}")
    parts.append(f"burn{args.burn_in}")
    parts.append(f"collect{args.collection_steps}")
    parts.append(f"lr{args.learning_rate:.1f}")
    parts.append(f"sh{args.sharpness:.1f}")
    parts.append(f"seed{args.seed}")
    
    return "_".join(parts) + ".pdf"


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Visualize phase transition: distance from center vs anchoring parameter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic phase transition plot (default: 10 runs per alpha)
  uv run python -m cli.phase_transition_cli --m 3 --n 15 --plot
  
  # With custom parameters
  uv run python -m cli.phase_transition_cli --m 3 --n 15 --runs 20 --burn-in 300 --collection-steps 100 --plot
  
  # With baselines
  uv run python -m cli.phase_transition_cli --m 3 --baselines "0*5,3*5,4*5" --runs 15 --plot
  
  # Save as PDF
  uv run python -m cli.phase_transition_cli --m 3 --n 15 --save
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
        help="Number of candidates (default: 3)"
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
        "--learning-rate",
        type=float,
        default=0.2,
        dest="learning_rate",
        help="Learning rate (0-1) for GTStrategy. Accepts --eta as alias. "
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
        "--burn-in",
        type=int,
        default=200,
        dest="burn_in",
        help="Number of burn-in steps before collection (default: 200)"
    )
    parser.add_argument(
        "--collection-steps",
        type=int,
        default=50,
        dest="collection_steps",
        help="Number of steps to collect and average (default: 50)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of independent runs per alpha value (default: 10)"
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom title for the plot"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual phase transition plot"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    args = parser.parse_args(args)
    
    # Handle default values
    if args.learning_rate is None:
        args.learning_rate = 0.2
    if args.sharpness is None:
        args.sharpness = 3.0
    
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
    
    # Print summary
    print(f"Phase Transition Experiment:")
    print(f"  Voters: {n}")
    print(f"  Candidates: {args.m}")
    print(f"  Burn-in steps: {args.burn_in}")
    print(f"  Collection steps: {args.collection_steps}")
    print(f"  Runs per alpha: {args.runs}")
    print(f"  Learning rate: {args.learning_rate}")
    print(f"  Sharpness: {args.sharpness}")
    print(f"  Seed: {args.seed}")
    print()
    
    # Generate plot
    if args.plot or args.save:
        fig = plot_phase_transition(
            n=n,
            m=args.m,
            eta=args.learning_rate,
            beta=args.sharpness,
            seed=args.seed,
            baselines=baselines,
            title=args.title,
            burn_in=args.burn_in,
            collection_steps=args.collection_steps,
            runs=args.runs,
        )
        
        # Save as PDF if requested
        if args.save:
            filename = generate_pdf_filename(args)
            plotter = BasePlot()
            filepath = plotter.save_figure(fig, filename)
            print(f"Plot saved to: {filepath}")
        
        # Show plot if requested
        if args.plot:
            plt.show()
    else:
        print("Note: Use --plot to display the plot or --save to export as PDF")


if __name__ == "__main__":
    main()
