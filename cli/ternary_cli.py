"""CLI for visualizing ternary trajectory plots before and after phase transition."""

import argparse
import matplotlib.pyplot as plt
from core.honest_reports import parse_baselines
from core.phase_transition import run_phase_transition_ternary
from core.cache_utils import (
    normalize_baselines_str,
    load_cached_run,
    save_cached_run,
    TERNARY_CACHE_SCHEMA_VERSION,
    get_run_path,
)
from plots.plot_ternary import plot_ternary_trajectories
from plots.BasePlot import BasePlot


def generate_pdf_filename(args):
    """
    Generate a descriptive PDF filename based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        str: Filename for the PDF file
    """
    parts = ["ternary"]
    parts.append(f"m{args.m}")
    parts.append(f"n{args.n}")
    parts.append(f"T{args.T}")
    parts.append(f"lr{args.learning_rate:.1f}")
    parts.append(f"sh{args.sharpness:.1f}")
    parts.append(f"seed{args.seed}")
    
    return "_".join(parts) + ".pdf"


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Visualize ternary trajectory plots comparing voting dynamics before and after phase transition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single ternary plot with specific alpha
  uv run python -m cli.ternary_cli --m 3 --n 15 --T 300 --anchor-strength 0.2 --plot
  
  # Two ternary plots (before and after threshold)
  uv run python -m cli.ternary_cli --m 3 --n 15 --T 300 --alpha-before 0.05 --alpha-after 0.60 --plot
  
  # With custom parameters
  uv run python -m cli.ternary_cli --m 3 --n 15 --T 300 --learning-rate 0.2 --sharpness 3.0 --seed 42 --anchor-strength 0.2 --plot
  
  # With baselines
  uv run python -m cli.ternary_cli --m 3 --baselines "0*5,3*5,4*5" --T 300 --anchor-strength 0.2 --plot
  
  # Save as PDF
  uv run python -m cli.ternary_cli --m 3 --n 15 --T 300 --anchor-strength 0.2 --save
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
        "--T",
        type=int,
        default=300,
        help="Total number of time steps (default: 300)"
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
        "--anchor-strength",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Anchoring strength parameter (0-1) for a single ternary plot. "
             "Accepts --alpha as alias. Use with --alpha-before and --alpha-after for two plots."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Alias for --anchor-strength (deprecated, use --anchor-strength instead)"
    )
    parser.add_argument(
        "--alpha-before",
        type=float,
        default=None,
        dest="alpha_before",
        help="Alpha value for 'before threshold' plot (0-1). Requires --alpha-after for two plots."
    )
    parser.add_argument(
        "--alpha-after",
        type=float,
        default=None,
        dest="alpha_after",
        help="Alpha value for 'after threshold' plot (0-1). Requires --alpha-before for two plots."
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
        help="Display a visual ternary trajectory plot"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    parser.add_argument(
        "--force-recompute",
        action="store_true",
        dest="force_recompute",
        help="Ignore any cached results and recompute simulations"
    )
    
    args = parser.parse_args(args)
    
    # Validate arguments
    if args.m != 3:
        parser.error("Ternary plot requires m == 3")
    
    if args.T < 1:
        parser.error("Number of time steps (--T) must be at least 1")
    
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
    
    # Validate alpha arguments
    if args.alpha_before is not None and args.alpha_after is not None:
        # Two plots mode
        if args.anchor_strength is not None:
            parser.error("Cannot use --anchor-strength (or --alpha) together with --alpha-before and --alpha-after")
        alpha = None
        alpha_before = args.alpha_before
        alpha_after = args.alpha_after
    elif args.anchor_strength is not None:
        # Single plot mode
        alpha = args.anchor_strength
        alpha_before = None
        alpha_after = None
    else:
        parser.error(
            "Must provide either --anchor-strength (or --alpha) for a single plot, "
            "or both --alpha-before and --alpha-after for two plots"
        )
    
    # Print summary
    print(f"Ternary Trajectory Plot:")
    print(f"  Voters: {n}")
    print(f"  Candidates: {args.m}")
    print(f"  Time steps: {args.T}")
    print(f"  Learning rate: {args.learning_rate}")
    print(f"  Sharpness: {args.sharpness}")
    print(f"  Seed: {args.seed}")
    if alpha is not None:
        print(f"  Alpha: {alpha}")
    else:
        print(f"  Alpha (before): {alpha_before}")
        print(f"  Alpha (after): {alpha_after}")
    print()
    
    # Generate plot
    if args.plot or args.save:
        # Determine which alpha(s) we need trajectories for
        if alpha is not None:
            alphas_for_cache = [float(alpha)]
            alpha_before_for_cache = None
            alpha_after_for_cache = None
        else:
            alphas_for_cache = [float(alpha_before), float(alpha_after)]
            alpha_before_for_cache = float(alpha_before)
            alpha_after_for_cache = float(alpha_after)

        params = {
            "n": int(n),
            "m": int(args.m),
            "seed": int(args.seed),
            "baselines": normalize_baselines_str(args.baselines) if args.baselines else None,
            "learning_rate": float(args.learning_rate),
            "sharpness": float(args.sharpness),
            "T": int(args.T),
            "alpha": float(alpha) if alpha is not None else None,
            "alpha_before": alpha_before_for_cache,
            "alpha_after": alpha_after_for_cache,
        }
        prefix_parts = [
            "ternary",
            f"m{args.m}",
            f"n{n}",
            f"T{args.T}",
            f"lr{args.learning_rate}",
            f"sh{args.sharpness}",
            f"seed{args.seed}",
        ]
        if alpha is not None:
            prefix_parts.append(f"alpha{alpha}")
        else:
            prefix_parts.append(f"alphaBefore{alpha_before}")
            prefix_parts.append(f"alphaAfter{alpha_after}")

        ternary_data = None
        if not args.force_recompute:
            ternary_data, _meta = load_cached_run(
                command="ternary",
                params=params,
                prefix_parts=prefix_parts,
                schema_version=TERNARY_CACHE_SCHEMA_VERSION,
            )
            if ternary_data is not None:
                run_dir = get_run_path(command="ternary", params=params, prefix_parts=prefix_parts)
                print(f"[cache] ternary hit: {run_dir}")

        if ternary_data is None:
            run_dir = get_run_path(command="ternary", params=params, prefix_parts=prefix_parts)
            print(f"[cache] ternary miss: {run_dir}")
            trajectories = []
            for a in alphas_for_cache:
                trajectories.append(
                    run_phase_transition_ternary(
                        a,
                        T=args.T,
                        n=n,
                        m=args.m,
                        eta=args.learning_rate,
                        beta=args.sharpness,
                        seed=args.seed,
                        baselines=baselines,
                    )
                )
            ternary_data = {"alphas": alphas_for_cache, "trajectories": trajectories}
            save_cached_run(
                command="ternary",
                params=params,
                prefix_parts=prefix_parts,
                schema_version=TERNARY_CACHE_SCHEMA_VERSION,
                data=ternary_data,
            )

        fig = plot_ternary_trajectories(
            n=n,
            m=args.m,
            eta=args.learning_rate,
            beta=args.sharpness,
            T=args.T,
            seed=args.seed,
            baselines=baselines,
            title=args.title,
            alpha=alpha,
            alpha_before=alpha_before,
            alpha_after=alpha_after,
            ternary_data=ternary_data,
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
