import argparse
import numpy as np
from core.honest_reports import generate_honest_reports, parse_baselines, format_rankings_readable
from core.rankings_core import generate_rankings, candidate_labels
from core.strategic_reports import generate_strategic_reports
from core.graph_utils import parse_edge_list
from plots.plot_voter_strategies import plot_voter_strategies
import matplotlib.pyplot as plt
import igraph


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
  
  # Using expected-score variant (deterministic dynamics)
  uv run python -m cli.strategic_reports_cli --m 3 --n 6 --T 5 --use-expected-score
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
        help="Total number of time steps. Plots will show t=0 to t=T-1 (T total time steps)"
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
        "--use-expected-score",
        action="store_true",
        dest="use_expected_score",
        help="Use expected-score variant where realized neighbor rankings are replaced by "
             "their mixed strategies, yielding deterministic dynamics. Only used when --strategy=gt_strategy. "
             "Default: False (uses sampled rankings)"
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
    parser.add_argument(
        "--show-payoffs",
        action="store_true",
        help="Display Layer 1 payoff analysis (S^uv = <p_tilde, r_v - r_u>) for each edge. "
             "Shows detailed breakdown per edge including rankings, rank vectors, and payoffs. "
             "Only available when --strategy=gt_strategy."
    )
    parser.add_argument(
        "--payoff-time",
        type=str,
        default="all",
        help="Time step(s) to show payoffs for when --show-payoffs is set. "
             "Options: 'all' (show all time steps), 'last' (show only last time step), "
             "or a comma-separated list of time step indices (e.g., '1,2,5'). "
             "Time steps are 1-indexed (t=1..T). Default: 'all'"
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
    # T represents total time steps, but strategy generates T+1 when T is passed
    # So we pass max(1, T-1) to get T total time steps (t=0 to t=T-1)
    # Use max(1, T-1) because strategy requires T >= 1
    try:
        results = generate_strategic_reports(
            honest_reports=honest_reports,
            T=max(1, args.T - 1),
            m=args.m,
            seed=args.seed,
            strategy=args.strategy,
            # GTStrategy parameters
            anchor_strength=args.anchor_strength,
            learning_rate=args.learning_rate,
            sharpness=args.sharpness,
            use_expected_score=args.use_expected_score,
            # SimilarityStrategy parameters
            distance_metric=args.distance_metric,
            # Graph topology
            graph=graph
        )
    except ValueError as e:
        parser.error(str(e))

    # Unpack standardized results dict
    strategies_full = results["reports"]
    # Slice to get only the first T time steps (t=0 to t=T-1)
    strategies = strategies_full[:, :args.T]
    selected_probs_full = results.get("selected_probs")
    selected_probs = selected_probs_full[:, :args.T] if selected_probs_full is not None else None
    
    # Get all possible rankings for output formatting
    all_rankings = generate_rankings(args.m, alphabetical=False)
    
    # Output results
    # Output format: for each voter, show their trajectory (t=0 to t=T-1)
    if args.alphabetical:
        labels = candidate_labels(args.m)
        for i in range(n):
            print(f"Voter {i}:")
            for t in range(args.T):
                ranking_idx = strategies[i, t]
                ranking = all_rankings[ranking_idx]
                alphabetical_ranking = tuple(labels[c] for c in ranking)
                ranking_str = ">".join(alphabetical_ranking)
                print(f"  t={t}: {ranking_str}")
    else:
        for i in range(n):
            print(f"Voter {i}:")
            for t in range(args.T):
                ranking_idx = strategies[i, t]
                ranking = all_rankings[ranking_idx]
                print(f"  t={t}: {ranking}")
    
    # Display Layer 1 payoff analysis if requested
    if args.show_payoffs:
        if args.strategy != "gt_strategy":
            parser.error("--show-payoffs is only available when --strategy=gt_strategy")
        
        # Get payoffs history and p_history from results
        payoffs_history = results.get("payoffs_history")
        p_history = results.get("p_history")
        
        if payoffs_history is None:
            print("\nWarning: Payoffs history not available. Payoff analysis requires GTStrategy.")
        else:
            # Parse payoff_time argument
            if args.payoff_time == "all":
                # Show all time steps (t=1 to t=T, which is indices 0 to T-1 in payoffs_history)
                time_steps_to_show = list(range(len(payoffs_history)))
            elif args.payoff_time == "last":
                # Show only last time step
                if len(payoffs_history) > 0:
                    time_steps_to_show = [len(payoffs_history) - 1]
                else:
                    time_steps_to_show = []
            else:
                # Parse comma-separated list of time step indices (1-indexed)
                try:
                    time_steps_to_show = [int(x.strip()) - 1 for x in args.payoff_time.split(',')]
                    # Validate: time steps should be in range [0, len(payoffs_history)-1]
                    # But user provides 1-indexed, so we subtract 1
                    for t_idx in time_steps_to_show:
                        if t_idx < 0 or t_idx >= len(payoffs_history):
                            parser.error(
                                f"Invalid time step in --payoff-time: {t_idx + 1}. "
                                f"Valid range is 1 to {len(payoffs_history)}"
                            )
                except ValueError as e:
                    parser.error(f"Invalid --payoff-time format: {args.payoff_time}. {e}")
            
            # Get or create graph for edge iteration
            if graph is None:
                # Complete graph: create temporary graph for edge iteration
                display_graph = igraph.Graph.Full(n, directed=False)
            else:
                display_graph = graph
            
            # Display payoffs for each requested time step
            for t_idx in time_steps_to_show:
                # t_idx is 0-indexed in payoffs_history (corresponds to time step t = t_idx + 1)
                # payoffs_history[t_idx] was computed at time step t = t_idx + 1 during generation
                t = t_idx + 1
                payoffs_dict = payoffs_history[t_idx]
                
                # Get p_tilde for this time step
                if p_history is not None and t_idx < len(p_history):
                    p_t = p_history[t_idx]
                    p_tilde = p_t - (1.0 / args.m)
                else:
                    # Fallback: compute from current rankings
                    p_tilde = None
                
                print(f"\n--- Layer 1 Analysis (Time Step t={t}) ---")
                if p_tilde is not None:
                    print(f"Centered Outcome (p_tilde): {np.round(p_tilde, 4)}")
                
                # Get current rankings for this time step
                # payoffs_history[t_idx] corresponds to time step t = t_idx + 1
                # strategies[:, t_idx + 1] contains rankings at time step t = t_idx + 1
                # But we need to check bounds since strategies might be sliced
                if t < strategies.shape[1]:
                    current_rankings = [all_rankings[strategies[i, t]] for i in range(n)]
                else:
                    # Fallback: use last available time step
                    last_t = strategies.shape[1] - 1
                    current_rankings = [all_rankings[strategies[i, last_t]] for i in range(n)]
                    print(f"  (Note: Using rankings from t={last_t} as t={t} is not available)")
                
                # Create mapping from ranking to rank vector (1-based indexing)
                ranking_to_rank_vector = {}
                for ranking in all_rankings:
                    rank_vector = np.zeros(args.m)
                    for rank_pos, candidate in enumerate(ranking):
                        rank_vector[candidate] = rank_pos + 1  # 1-based indexing
                    ranking_to_rank_vector[ranking] = rank_vector
                
                # Display payoffs for each edge
                # Sort edges for consistent output
                edges_list = sorted(payoffs_dict.keys())
                
                for (u, v) in edges_list:
                    payoff = payoffs_dict[(u, v)]
                    
                    # Get rankings and rank vectors
                    ranking_u = current_rankings[u]
                    ranking_v = current_rankings[v]
                    r_u = ranking_to_rank_vector[ranking_u]
                    r_v = ranking_to_rank_vector[ranking_v]
                    diff_vu = r_v - r_u
                    
                    # Format rankings for display
                    if args.alphabetical:
                        labels = candidate_labels(args.m)
                        ranking_u_str = ">".join(labels[c] for c in ranking_u)
                        ranking_v_str = ">".join(labels[c] for c in ranking_v)
                    else:
                        ranking_u_str = str(ranking_u)
                        ranking_v_str = str(ranking_v)
                    
                    print(f"\nEdge ({u}, {v}):")
                    print(f"  Ranking {u}: {ranking_u_str} -> r={r_u}")
                    print(f"  Ranking {v}: {ranking_v_str} -> r={r_v}")
                    print(f"  Diff (r_{v} - r_{u}): {diff_vu}")
                    print(f"  Payoff S^{u}{v}: {payoff:.4f}")
    
    # Plot if requested
    if args.plot or args.save:
        # Plot the heatmap showing trajectory over T time steps (t=0 to t=T-1)
        ax = plot_voter_strategies(
            strategies,
            all_rankings,
            labels=None,
            ax=None,
            show_integers=False,
            title=(f"Strategic Reports Evolution\n({n} voters, {args.m} candidates, {args.T} time steps)"),
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
