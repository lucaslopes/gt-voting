"""CLI for visualizing probability distributions as proportion plots."""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from core.honest_reports import generate_honest_reports, parse_baselines
from core.rankings_core import generate_rankings, candidate_labels
from core.strategic_reports import generate_strategic_reports
from core.aggregator_core import aggregate_rankings
from plots.plot_proportions import plot_proportions
from plots.BasePlot import BasePlot
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
        help="Total number of time steps. Plots will show t=0 to t=T-1 (T total time steps). "
             "If provided, uses strategic reports mode."
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
    parser.add_argument(
        "--time-average",
        action="store_true",
        help="Plot time-averaged outcomes \\hat{p}^t instead of instantaneous outcomes p^t. "
             "Only available for strategic reports mode (when --T is provided) and when using GTStrategy. "
             "Time-averaged outcomes are defined as \\hat{p}^t = (1/t) * sum_{tau=1}^t p^tau."
    )
    parser.add_argument(
        "--show-both",
        action="store_true",
        help="Display both instantaneous and time-averaged outcomes side-by-side. "
             "Only available for strategic reports mode (when --T is provided) and when using GTStrategy. "
             "Creates two subplots: left shows instantaneous p^t, right shows time-averaged \\hat{p}^t."
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
        # T represents total time steps (t=0 to t=T-1, so T total steps)
        # Strategy generates reports for t=0 to t=T (T+1 steps) and p_history/p_avg_history for t=1 to t=T (T entries)
        # So we pass args.T to get T iterations for p_history/p_avg_history (t=1 to t=T)
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
        strategies_full = strategies_result["reports"]
        # Slice to get t=0 to t=T (T+1 time steps) to match p_avg_history which covers t=1 to t=T
        strategies = strategies_full[:, :args.T + 1]
        
        # Extract p_history and p_avg_history if available (from GTStrategy)
        p_history_full = strategies_result.get("p_history")
        p_avg_history_full = strategies_result.get("p_avg_history")
        # p_history and p_avg_history have shape [T, m] for t=1 to t=T (where T was passed to generate_strategic_reports)
        # We want the first args.T entries (for t=1 to t=args.T)
        p_history = p_history_full[:args.T] if p_history_full is not None else None
        p_avg_history = p_avg_history_full[:args.T] if p_avg_history_full is not None else None
        
        # Validate time-averaging flags
        if args.time_average or args.show_both:
            if args.strategy != "gt_strategy":
                parser.error("--time-average and --show-both are only available when using GTStrategy (--strategy=gt_strategy)")
            if p_avg_history is None:
                parser.error("Time-averaged outcomes not available. This may occur if the strategy doesn't support time-averaging.")
        
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
        if p_history is not None and p_avg_history is not None:
            print(f"  Time-averaging: Available (instantaneous and time-averaged outcomes tracked)")
        print()
        
        # Print probabilities for each time step
        if args.time_average and p_avg_history is not None:
            # Print time-averaged outcomes
            # p_avg_history was computed with GT mechanism, so if user wants GT, use it directly
            # Otherwise, we need to recompute from strategies
            if args.mechanism.upper() == "GT":
                # Use precomputed p_avg_history (computed with GT)
                # First, print t=0 (instantaneous, no averaging yet)
                rankings_at_t0 = [all_rankings[strategies[i, 0]] for i in range(n)]
                probs_t0 = aggregate_rankings(rankings_at_t0, mechanism=args.mechanism)
                print(f"Time-averaged \\hat{{p}}^0: {probs_t0}")
                # Then print time-averaged outcomes for t=1 to t=T-1 (from p_avg_history)
                for t_idx, p_avg in enumerate(p_avg_history):
                    print(f"Time-averaged \\hat{{p}}^{t_idx+1}: {p_avg}")
            else:
                # User wants different mechanism, compute time-averaged from strategies
                p_sum = np.zeros(args.m, dtype=float)
                # Print t=0 (instantaneous, no averaging yet)
                rankings_at_t0 = [all_rankings[strategies[i, 0]] for i in range(n)]
                probs_t0 = aggregate_rankings(rankings_at_t0, mechanism=args.mechanism)
                print(f"Time-averaged \\hat{{p}}^0: {probs_t0}")
                # Compute and print time-averaged for t=1 to t=T-1
                for t in range(1, args.T):
                    rankings_at_t = [all_rankings[strategies[i, t]] for i in range(n)]
                    probs = aggregate_rankings(rankings_at_t, mechanism=args.mechanism)
                    p_sum += np.array(probs)
                    p_avg = p_sum / t
                    print(f"Time-averaged \\hat{{p}}^{t}: {p_avg}")
        else:
            # Print instantaneous outcomes for each time step (t=0 to t=T)
            # strategies has shape [n, T+1] with columns for t=0 to t=T
            for t in range(args.T + 1):
                rankings_at_t = [all_rankings[strategies[i, t]] for i in range(n)]
                probs = aggregate_rankings(rankings_at_t, mechanism=args.mechanism)
                print(f"Time step t={t}: {probs}")
        
        # Print time-averaged outcomes if available and not already printed
        if p_avg_history is not None and not args.time_average and not args.show_both:
            print("\nTime-averaged outcomes (use --time-average to plot):")
            for t_idx, p_avg in enumerate(p_avg_history):
                print(f"Time-averaged \\hat{{p}}^{t_idx+1}: {p_avg}")
        
        # Plot if requested
        if args.plot or args.save:
            if args.show_both:
                # Create side-by-side subplots
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 8))
                
                # Left plot: instantaneous outcomes
                ax1 = plot_proportions(
                    strategies,
                    m=args.m,
                    all_rankings=all_rankings,
                    labels=None,
                    mechanism=args.mechanism,
                    ax=ax1,
                    title=args.title if args.title else "Instantaneous Outcomes p^t",
                    show_integers=args.show_integers,
                    use_time_average=False,
                    p_history=p_history,
                    p_avg_history=p_avg_history
                )
                
                # Right plot: time-averaged outcomes
                ax2 = plot_proportions(
                    strategies,
                    m=args.m,
                    all_rankings=all_rankings,
                    labels=None,
                    mechanism=args.mechanism,
                    ax=ax2,
                    title=args.title if args.title else "Time-Averaged Outcomes \\hat{p}^t",
                    show_integers=args.show_integers,
                    use_time_average=True,
                    p_history=p_history,
                    p_avg_history=p_avg_history
                )
                
                plt.tight_layout()
                
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
                # Single plot
                ax = plot_proportions(
                    strategies,
                    m=args.m,
                    all_rankings=all_rankings,
                    labels=None,
                    mechanism=args.mechanism,
                    ax=None,
                    title=args.title,
                    show_integers=args.show_integers,
                    use_time_average=args.time_average,
                    p_history=p_history,
                    p_avg_history=p_avg_history
                )
                
                # Save as PDF if requested
                if args.save:
                    filename = generate_pdf_filename(args)
                    plotter = BasePlot()
                    fig = ax.figure
                    filepath = plotter.save_figure(fig, filename)
                    print(f"Plot saved to: {filepath}")
                
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
                plotter = BasePlot()
                fig = ax.figure
                filepath = plotter.save_figure(fig, filename)
                print(f"Plot saved to: {filepath}")
            
            # Show plot if requested
            if args.plot:
                plt.show()


if __name__ == "__main__":
    main()
