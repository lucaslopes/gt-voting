"""CLI for combined dashboard view with phase transition, strategy heatmap, ternary plots, and text explanation."""

import argparse
import matplotlib.pyplot as plt
from core.honest_reports import parse_baselines
from core.dashboard_core import run_dashboard_simulation
from plots.plot_dashboard import plot_dashboard
from plots.BasePlot import BasePlot


def generate_pdf_filename(args):
    """
    Generate a descriptive PDF filename based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        str: Filename for the PDF file
    """
    parts = ["dashboard"]
    parts.append(f"m{args.m}")
    parts.append(f"n{args.n}")
    parts.append(f"T{args.T}")
    parts.append(f"lr{args.learning_rate:.1f}")
    parts.append(f"sh{args.sharpness:.1f}")
    parts.append(f"seed{args.seed}")
    
    return "_".join(parts) + ".pdf"


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Combined dashboard view with phase transition, strategy heatmap, ternary plots, and text explanation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic dashboard (default: 15 voters, 3 candidates)
  uv run python -m cli dashboard --plot
  
  # With custom parameters
  uv run python -m cli dashboard --n 20 --m 3 --seed 42 --plot
  
  # With baselines
  uv run python -m cli dashboard --baselines "0*5,3*5,4*5" --plot
  
  # Save as PDF
  uv run python -m cli dashboard --save
  
  # Both plot and save
  uv run python -m cli dashboard --plot --save
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
        help="Number of candidates (default: 3, must be 3 for ternary plots)"
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
        "--T",
        type=int,
        default=300,
        help="Total number of time steps for heatmap/ternary (default: 300)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual dashboard plot"
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
    print(f"Dashboard Experiment:")
    print(f"  Voters: {n}")
    print(f"  Candidates: {args.m}")
    print(f"  Time steps: {args.T}")
    print(f"  Learning rate: {args.learning_rate}")
    print(f"  Sharpness: {args.sharpness}")
    print(f"  Seed: {args.seed}")
    print()
    
    # Generate plot
    if args.plot or args.save:
        # Run simulation
        data = run_dashboard_simulation(
            n=n,
            m=args.m,
            seed=args.seed,
            baselines=baselines,
            eta=args.learning_rate,
            beta=args.sharpness,
            T=args.T,
        )
        
        # Create dashboard plot
        fig = plot_dashboard(data=data, n=n, m=args.m, seed=args.seed)
        
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
