"""Main CLI entry point for ranking tools."""

import argparse
from cli.rankings_cli import main as rankings_main
from cli.honest_reports_cli import main as honest_reports_main
from cli.strategic_reports_cli import main as strategic_reports_main
from cli.proportions_cli import main as proportions_main
from cli.ternary_cli import main as ternary_main
from cli.phase_transition_cli import main as phase_transition_main
from cli.dashboard_cli import main as dashboard_main
from mechanisms import list_mechanisms


def main():
    """Unified CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(
        description="GT Voting System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)
    
    # Rankings subcommand
    rankings_parser = subparsers.add_parser(
        'rankings',
        help='Generate and display all possible candidate rankings',
        description='Generate and display all possible candidate rankings'
    )
    rankings_parser.add_argument(
        "--m",
        type=int,
        default=None,
        help="Number of candidates (required if --candidates not provided)"
    )
    rankings_parser.add_argument(
        "--candidates",
        type=int,
        default=None,
        dest="m",
        help="Number of candidates (alternative to --m)"
    )
    rankings_parser.add_argument(
        "--alphabetical",
        action="store_true",
        help="Output rankings in alphabetical format (default: integer format)"
    )
    rankings_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual plot of all rankings (in addition to terminal output)"
    )
    rankings_parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    rankings_parser.add_argument(
        "--layout",
        type=str,
        choices=['horizontal', 'vertical', 'matrix', 'auto'],
        default='auto',
        help="Layout style for the plot: 'horizontal' (single row), 'vertical' (single column), 'matrix' (grid), or 'auto' (default, chooses based on number of rankings)"
    )
    
    # Honest reports subcommand
    honest_reports_parser = subparsers.add_parser(
        'honest-reports',
        help='Generate honest reports from baselines or seed',
        description='Generate honest reports from baselines or seed'
    )
    honest_reports_parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
    )
    honest_reports_parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3, required to validate baseline indices)"
    )
    honest_reports_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0, used when --baselines not provided)"
    )
    honest_reports_parser.add_argument(
        "--baselines",
        type=str,
        default=None,
        help="Baseline permutation indices. Supports two formats:\n"
             "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
             "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
             "Indices refer to positions in the sorted list from generate_rankings(m).\n"
             "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly."
    )
    honest_reports_parser.add_argument(
        "--alphabetical",
        action="store_true",
        help="Output rankings in alphabetical format (default: integer format)"
    )
    honest_reports_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual heatmap of voter strategies (in addition to terminal output)"
    )
    honest_reports_parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    # Strategic reports subcommand
    strategic_reports_parser = subparsers.add_parser(
        'strategic-reports',
        help='Generate strategic reports that evolve over T iterations',
        description='Generate strategic reports that evolve over T iterations'
    )
    strategic_reports_parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
    )
    strategic_reports_parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3, required to validate baseline indices)"
    )
    strategic_reports_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0, used when --baselines not provided)"
    )
    strategic_reports_parser.add_argument(
        "--baselines",
        type=str,
        default=None,
        help="Baseline permutation indices. Supports two formats:\n"
             "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
             "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
             "Indices refer to positions in the sorted list from generate_rankings(m).\n"
             "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly."
    )
    strategic_reports_parser.add_argument(
        "--T",
        type=int,
        required=True,
        help="Total number of time steps. Plots will show t=0 to t=T-1 (T total time steps)"
    )
    strategic_reports_parser.add_argument(
        "--strategy",
        type=str,
        default="gt_strategy",
        help="Strategy to use for evolving reports (default: gt_strategy). "
             "Available: gt_strategy, similarity_strategy"
    )
    # GTStrategy parameters
    strategic_reports_parser.add_argument(
        "--anchor-strength",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Anchoring strength parameter (0-1). Controls how much voters stick to baseline. "
             "Accepts --alpha as alias. Default: 0.1 for GTStrategy, 0.5 for SimilarityStrategy"
    )
    strategic_reports_parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Alias for --anchor-strength (deprecated, use --anchor-strength instead)"
    )
    strategic_reports_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.2,
        dest="learning_rate",
        help="Learning rate (0-1) for GTStrategy. Controls update speed. "
             "Accepts --eta as alias. Only used when --strategy=gt_strategy (default: 0.2)"
    )
    strategic_reports_parser.add_argument(
        "--eta",
        type=float,
        default=None,
        dest="learning_rate",
        help="Alias for --learning-rate (deprecated, use --learning-rate instead)"
    )
    strategic_reports_parser.add_argument(
        "--sharpness",
        type=float,
        default=3.0,
        dest="sharpness",
        help="Sharpness parameter (>0) for GTStrategy. Controls exploration vs exploitation. "
             "Accepts --beta as alias. Only used when --strategy=gt_strategy (default: 3.0)"
    )
    strategic_reports_parser.add_argument(
        "--beta",
        type=float,
        default=None,
        dest="sharpness",
        help="Alias for --sharpness (deprecated, use --sharpness instead)"
    )
    strategic_reports_parser.add_argument(
        "--distance-metric",
        type=str,
        default="spearman",
        help="Distance metric for SimilarityStrategy. Only used when --strategy=similarity_strategy. "
             "Available: spearman, kendall_tau (default: spearman)"
    )
    strategic_reports_parser.add_argument(
        "--alphabetical",
        action="store_true",
        help="Output rankings in alphabetical format (default: integer format)"
    )
    strategic_reports_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual heatmap of voter strategy evolution over T iterations"
    )
    strategic_reports_parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    # Proportions subcommand
    proportions_parser = subparsers.add_parser(
        'proportions',
        help='Visualize probability distributions as proportion plots',
        description='Visualize probability distributions as proportion plots (stacked area charts)'
    )
    proportions_parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3)"
    )
    proportions_parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
    )
    proportions_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0, used when --baselines not provided)"
    )
    proportions_parser.add_argument(
        "--baselines",
        type=str,
        default=None,
        help="Baseline permutation indices. Supports two formats:\n"
             "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
             "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
             "Indices refer to positions in the sorted list from generate_rankings(m).\n"
             "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly."
    )
    proportions_parser.add_argument(
        "--T",
        type=int,
        default=None,
        help="Total number of time steps. Plots will show t=0 to t=T-1 (T total time steps). "
             "If provided, shows evolution over time. If not provided, shows single election outcome."
    )
    proportions_parser.add_argument(
        "--strategy",
        type=str,
        default="gt_strategy",
        help="Strategy to use for evolving reports. Only used when --T is provided. "
             "Available: gt_strategy, similarity_strategy (default: gt_strategy)"
    )
    # GTStrategy parameters
    proportions_parser.add_argument(
        "--anchor-strength",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Anchoring parameter (0-1). Controls how much voters stick to baseline. "
             "Accepts --alpha as alias. Only used when --T is provided. "
             "Default: 0.1 for GTStrategy, 0.5 for SimilarityStrategy"
    )
    proportions_parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Alias for --anchor-strength (deprecated, use --anchor-strength instead)"
    )
    proportions_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.2,
        dest="learning_rate",
        help="Learning rate (0-1) for GTStrategy. Accepts --eta as alias. "
             "Only used when --T is provided and --strategy=gt_strategy. "
             "Controls update speed (default: 0.2)"
    )
    proportions_parser.add_argument(
        "--eta",
        type=float,
        default=None,
        dest="learning_rate",
        help="Alias for --learning-rate (deprecated, use --learning-rate instead)"
    )
    proportions_parser.add_argument(
        "--sharpness",
        type=float,
        default=3.0,
        dest="sharpness",
        help="Sharpness parameter (>0) for GTStrategy. Accepts --beta as alias. "
             "Only used when --T is provided and --strategy=gt_strategy. "
             "Controls exploration vs exploitation (default: 3.0)"
    )
    proportions_parser.add_argument(
        "--beta",
        type=float,
        default=None,
        dest="sharpness",
        help="Alias for --sharpness (deprecated, use --sharpness instead)"
    )
    proportions_parser.add_argument(
        "--distance-metric",
        type=str,
        default="spearman",
        help="Distance metric for SimilarityStrategy. Only used when --T is provided and --strategy=similarity_strategy. "
             "Available: spearman, kendall_tau (default: spearman)"
    )
    # Get available mechanisms for help text
    available_mechanisms = list_mechanisms()
    mechanism_help = f"Aggregation mechanism (default: GT). Available: {', '.join(available_mechanisms)}"
    
    proportions_parser.add_argument(
        "--mechanism",
        type=str,
        default="GT",
        help=mechanism_help
    )
    proportions_parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom title for the plot"
    )
    proportions_parser.add_argument(
        "--show-integers",
        action="store_true",
        help="Show candidate integers instead of alphabetical labels in legend"
    )
    proportions_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual proportion plot (stacked area chart)"
    )
    proportions_parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    proportions_parser.add_argument(
        "--time-average",
        action="store_true",
        dest="time_average",
        help="Plot time-averaged outcomes \\hat{p}^t instead of instantaneous outcomes p^t. "
             "Only available for strategic reports mode (when --T is provided) and when using GTStrategy. "
             "Time-averaged outcomes are defined as \\hat{p}^t = (1/t) * sum_{tau=1}^t p^tau."
    )
    proportions_parser.add_argument(
        "--show-both",
        action="store_true",
        dest="show_both",
        help="Display both instantaneous and time-averaged outcomes side-by-side. "
             "Only available for strategic reports mode (when --T is provided) and when using GTStrategy. "
             "Creates two subplots: left shows instantaneous p^t, right shows time-averaged \\hat{p}^t."
    )
    
    # Ternary subcommand
    ternary_parser = subparsers.add_parser(
        'ternary',
        help='Visualize ternary trajectory plots before and after phase transition',
        description='Visualize ternary trajectory plots comparing voting dynamics before and after phase transition threshold'
    )
    ternary_parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
    )
    ternary_parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3, must be 3 for ternary plots)"
    )
    ternary_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0, used when --baselines not provided)"
    )
    ternary_parser.add_argument(
        "--baselines",
        type=str,
        default=None,
        help="Baseline permutation indices. Supports two formats:\n"
             "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
             "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
             "Indices refer to positions in the sorted list from generate_rankings(m).\n"
             "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly."
    )
    ternary_parser.add_argument(
        "--T",
        type=int,
        default=300,
        help="Total number of time steps (default: 300)"
    )
    ternary_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.2,
        dest="learning_rate",
        help="Learning rate (0-1) for GTStrategy. Accepts --eta as alias. "
             "Controls update speed (default: 0.2)"
    )
    ternary_parser.add_argument(
        "--eta",
        type=float,
        default=None,
        dest="learning_rate",
        help="Alias for --learning-rate (deprecated, use --learning-rate instead)"
    )
    ternary_parser.add_argument(
        "--sharpness",
        type=float,
        default=3.0,
        dest="sharpness",
        help="Sharpness parameter (>0) for GTStrategy. Accepts --beta as alias. "
             "Controls exploration vs exploitation (default: 3.0)"
    )
    ternary_parser.add_argument(
        "--beta",
        type=float,
        default=None,
        dest="sharpness",
        help="Alias for --sharpness (deprecated, use --sharpness instead)"
    )
    ternary_parser.add_argument(
        "--anchor-strength",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Anchoring strength parameter (0-1) for a single ternary plot. "
             "Accepts --alpha as alias. Use with --alpha-before and --alpha-after for two plots."
    )
    ternary_parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        dest="anchor_strength",
        help="Alias for --anchor-strength (deprecated, use --anchor-strength instead)"
    )
    ternary_parser.add_argument(
        "--alpha-before",
        type=float,
        default=None,
        dest="alpha_before",
        help="Alpha value for 'before threshold' plot (0-1). Requires --alpha-after for two plots."
    )
    ternary_parser.add_argument(
        "--alpha-after",
        type=float,
        default=None,
        dest="alpha_after",
        help="Alpha value for 'after threshold' plot (0-1). Requires --alpha-before for two plots."
    )
    ternary_parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom title for the plot"
    )
    ternary_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual ternary trajectory plot"
    )
    ternary_parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    # Phase transition subcommand
    phase_transition_parser = subparsers.add_parser(
        'phase-transition',
        help='Visualize phase transition: distance from center vs anchoring parameter',
        description='Visualize phase transition experiment showing distance from center (tie) vs anchoring parameter (α)'
    )
    phase_transition_parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
    )
    phase_transition_parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3)"
    )
    phase_transition_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0, used when --baselines not provided)"
    )
    phase_transition_parser.add_argument(
        "--baselines",
        type=str,
        default=None,
        help="Baseline permutation indices. Supports two formats:\n"
             "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
             "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
             "Indices refer to positions in the sorted list from generate_rankings(m).\n"
             "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly."
    )
    phase_transition_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.2,
        dest="learning_rate",
        help="Learning rate (0-1) for GTStrategy. Accepts --eta as alias. "
             "Controls update speed (default: 0.2)"
    )
    phase_transition_parser.add_argument(
        "--eta",
        type=float,
        default=None,
        dest="learning_rate",
        help="Alias for --learning-rate (deprecated, use --learning-rate instead)"
    )
    phase_transition_parser.add_argument(
        "--sharpness",
        type=float,
        default=3.0,
        dest="sharpness",
        help="Sharpness parameter (>0) for GTStrategy. Accepts --beta as alias. "
             "Controls exploration vs exploitation (default: 3.0)"
    )
    phase_transition_parser.add_argument(
        "--beta",
        type=float,
        default=None,
        dest="sharpness",
        help="Alias for --sharpness (deprecated, use --sharpness instead)"
    )
    phase_transition_parser.add_argument(
        "--burn-in",
        type=int,
        default=200,
        dest="burn_in",
        help="Number of burn-in steps before collection (default: 200)"
    )
    phase_transition_parser.add_argument(
        "--collection-steps",
        type=int,
        default=50,
        dest="collection_steps",
        help="Number of steps to collect and average (default: 50)"
    )
    phase_transition_parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of independent runs per alpha value (default: 10)"
    )
    phase_transition_parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom title for the plot"
    )
    phase_transition_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual phase transition plot"
    )
    phase_transition_parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    # Dashboard subcommand
    dashboard_parser = subparsers.add_parser(
        'dashboard',
        help='Combined dashboard view with phase transition, strategy heatmap, ternary plots, and text explanation',
        description='Combined dashboard view with phase transition, strategy heatmap, ternary plots, and text explanation'
    )
    dashboard_parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of voters (default: 15, or inferred from --baselines if provided)"
    )
    dashboard_parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Number of candidates (default: 3, must be 3 for ternary plots)"
    )
    dashboard_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0, used when --baselines not provided)"
    )
    dashboard_parser.add_argument(
        "--baselines",
        type=str,
        default=None,
        help="Baseline permutation indices. Supports two formats:\n"
             "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
             "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
             "Indices refer to positions in the sorted list from generate_rankings(m).\n"
             "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly."
    )
    dashboard_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.2,
        dest="learning_rate",
        help="Learning rate (0-1) for GTStrategy. Accepts --eta as alias. "
             "Controls update speed (default: 0.2)"
    )
    dashboard_parser.add_argument(
        "--eta",
        type=float,
        default=None,
        dest="learning_rate",
        help="Alias for --learning-rate (deprecated, use --learning-rate instead)"
    )
    dashboard_parser.add_argument(
        "--sharpness",
        type=float,
        default=3.0,
        dest="sharpness",
        help="Sharpness parameter (>0) for GTStrategy. Accepts --beta as alias. "
             "Controls exploration vs exploitation (default: 3.0)"
    )
    dashboard_parser.add_argument(
        "--beta",
        type=float,
        default=None,
        dest="sharpness",
        help="Alias for --sharpness (deprecated, use --sharpness instead)"
    )
    dashboard_parser.add_argument(
        "--T",
        type=int,
        default=300,
        help="Total number of time steps for heatmap/ternary (default: 300)"
    )
    dashboard_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display a visual dashboard plot"
    )
    dashboard_parser.add_argument(
        "--save",
        action="store_true",
        help="Export the plot as a high-quality PDF file"
    )
    
    args = parser.parse_args()
    
    # Handle default values based on strategy
    if args.command == 'strategic-reports':
        if args.anchor_strength is None:
            args.anchor_strength = 0.1 if args.strategy == "gt_strategy" else 0.5
        if args.learning_rate is None:
            args.learning_rate = 0.2
        if args.sharpness is None:
            args.sharpness = 3.0
    elif args.command == 'proportions':
        if args.T is not None and args.anchor_strength is None:
            args.anchor_strength = 0.1 if args.strategy == "gt_strategy" else 0.5
        if args.T is not None:
            if args.learning_rate is None:
                args.learning_rate = 0.2
            if args.sharpness is None:
                args.sharpness = 3.0
    elif args.command == 'ternary':
        if args.learning_rate is None:
            args.learning_rate = 0.2
        if args.sharpness is None:
            args.sharpness = 3.0
    elif args.command == 'phase-transition':
        if args.learning_rate is None:
            args.learning_rate = 0.2
        if args.sharpness is None:
            args.sharpness = 3.0
    elif args.command == 'dashboard':
        if args.learning_rate is None:
            args.learning_rate = 0.2
        if args.sharpness is None:
            args.sharpness = 3.0
    
    if args.command == 'rankings':
        # Build argument list for rankings CLI
        rankings_args = []
        if args.m is not None:
            rankings_args.extend(['--m', str(args.m)])
        if args.alphabetical:
            rankings_args.append('--alphabetical')
        if args.plot:
            rankings_args.append('--plot')
        if args.save:
            rankings_args.append('--save')
        if args.layout != 'auto':
            rankings_args.extend(['--layout', args.layout])
        rankings_main(rankings_args)
    elif args.command == 'honest-reports':
        # Build argument list for honest reports CLI
        honest_reports_args = []
        if args.n is not None:
            honest_reports_args.extend(['--n', str(args.n)])
        honest_reports_args.extend(['--m', str(args.m)])
        honest_reports_args.extend(['--seed', str(args.seed)])
        if args.baselines is not None:
            honest_reports_args.extend(['--baselines', args.baselines])
        if args.alphabetical:
            honest_reports_args.append('--alphabetical')
        if args.plot:
            honest_reports_args.append('--plot')
        if args.save:
            honest_reports_args.append('--save')
        honest_reports_main(honest_reports_args)
    elif args.command == 'strategic-reports':
        # Build argument list for strategic reports CLI
        strategic_reports_args = []
        if args.n is not None:
            strategic_reports_args.extend(['--n', str(args.n)])
        strategic_reports_args.extend(['--m', str(args.m)])
        strategic_reports_args.extend(['--seed', str(args.seed)])
        if args.baselines is not None:
            strategic_reports_args.extend(['--baselines', args.baselines])
        # T represents total time steps, but strategy generates T+1 when T is passed
        # So we pass T-1 to get T total time steps (t=0 to t=T-1)
        strategic_reports_args.extend(['--T', str(args.T)])
        strategic_reports_args.extend(['--strategy', args.strategy])
        strategic_reports_args.extend(['--anchor-strength', str(args.anchor_strength)])
        strategic_reports_args.extend(['--learning-rate', str(args.learning_rate)])
        strategic_reports_args.extend(['--sharpness', str(args.sharpness)])
        strategic_reports_args.extend(['--distance-metric', args.distance_metric])
        if args.alphabetical:
            strategic_reports_args.append('--alphabetical')
        if args.plot:
            strategic_reports_args.append('--plot')
        if args.save:
            strategic_reports_args.append('--save')
        strategic_reports_main(strategic_reports_args)
    elif args.command == 'proportions':
        # Build argument list for proportions CLI
        proportions_args = []
        proportions_args.extend(['--m', str(args.m)])
        if args.n is not None:
            proportions_args.extend(['--n', str(args.n)])
        proportions_args.extend(['--seed', str(args.seed)])
        if args.baselines is not None:
            proportions_args.extend(['--baselines', args.baselines])
        if args.T is not None:
            proportions_args.extend(['--T', str(args.T)])
            proportions_args.extend(['--strategy', args.strategy])
            proportions_args.extend(['--anchor-strength', str(args.anchor_strength)])
            proportions_args.extend(['--learning-rate', str(args.learning_rate)])
            proportions_args.extend(['--sharpness', str(args.sharpness)])
            proportions_args.extend(['--distance-metric', args.distance_metric])
        proportions_args.extend(['--mechanism', args.mechanism])
        if args.title is not None:
            proportions_args.extend(['--title', args.title])
        if args.show_integers:
            proportions_args.append('--show-integers')
        if args.plot:
            proportions_args.append('--plot')
        if args.save:
            proportions_args.append('--save')
        if hasattr(args, 'time_average') and args.time_average:
            proportions_args.append('--time-average')
        if hasattr(args, 'show_both') and args.show_both:
            proportions_args.append('--show-both')
        proportions_main(proportions_args)
    elif args.command == 'ternary':
        # Build argument list for ternary CLI
        ternary_args = []
        if args.n is not None:
            ternary_args.extend(['--n', str(args.n)])
        ternary_args.extend(['--m', str(args.m)])
        ternary_args.extend(['--seed', str(args.seed)])
        if args.baselines is not None:
            ternary_args.extend(['--baselines', args.baselines])
        ternary_args.extend(['--T', str(args.T)])
        ternary_args.extend(['--learning-rate', str(args.learning_rate)])
        ternary_args.extend(['--sharpness', str(args.sharpness)])
        if hasattr(args, 'anchor_strength') and args.anchor_strength is not None:
            ternary_args.extend(['--anchor-strength', str(args.anchor_strength)])
        if hasattr(args, 'alpha_before') and args.alpha_before is not None:
            ternary_args.extend(['--alpha-before', str(args.alpha_before)])
        if hasattr(args, 'alpha_after') and args.alpha_after is not None:
            ternary_args.extend(['--alpha-after', str(args.alpha_after)])
        if args.title is not None:
            ternary_args.extend(['--title', args.title])
        if args.plot:
            ternary_args.append('--plot')
        if args.save:
            ternary_args.append('--save')
        ternary_main(ternary_args)
    elif args.command == 'phase-transition':
        # Build argument list for phase transition CLI
        phase_transition_args = []
        if args.n is not None:
            phase_transition_args.extend(['--n', str(args.n)])
        phase_transition_args.extend(['--m', str(args.m)])
        phase_transition_args.extend(['--seed', str(args.seed)])
        if args.baselines is not None:
            phase_transition_args.extend(['--baselines', args.baselines])
        phase_transition_args.extend(['--learning-rate', str(args.learning_rate)])
        phase_transition_args.extend(['--sharpness', str(args.sharpness)])
        if hasattr(args, 'burn_in'):
            phase_transition_args.extend(['--burn-in', str(args.burn_in)])
        if hasattr(args, 'collection_steps'):
            phase_transition_args.extend(['--collection-steps', str(args.collection_steps)])
        if hasattr(args, 'runs'):
            phase_transition_args.extend(['--runs', str(args.runs)])
        if args.title is not None:
            phase_transition_args.extend(['--title', args.title])
        if args.plot:
            phase_transition_args.append('--plot')
        if args.save:
            phase_transition_args.append('--save')
        phase_transition_main(phase_transition_args)
    elif args.command == 'dashboard':
        # Build argument list for dashboard CLI
        dashboard_args = []
        if args.n is not None:
            dashboard_args.extend(['--n', str(args.n)])
        dashboard_args.extend(['--m', str(args.m)])
        dashboard_args.extend(['--seed', str(args.seed)])
        if args.baselines is not None:
            dashboard_args.extend(['--baselines', args.baselines])
        dashboard_args.extend(['--learning-rate', str(args.learning_rate)])
        dashboard_args.extend(['--sharpness', str(args.sharpness)])
        dashboard_args.extend(['--T', str(args.T)])
        if args.plot:
            dashboard_args.append('--plot')
        if args.save:
            dashboard_args.append('--save')
        dashboard_main(dashboard_args)


if __name__ == "__main__":
    main()
