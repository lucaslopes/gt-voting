"""Main CLI entry point for ranking tools."""

import argparse
from cli.rankings_cli import main as rankings_main
from cli.honest_reports_cli import main as honest_reports_main
from cli.strategic_reports_cli import main as strategic_reports_main
from cli.proportions_cli import main as proportions_main


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
        help="Number of iterations (time steps) for strategic evolution"
    )
    strategic_reports_parser.add_argument(
        "--anchor",
        type=float,
        default=0.5,
        help="Anchor parameter (0-1) controlling how closely reports stay to honest reports. "
             "1.0 = reports never change, 0.0 = reports can change completely randomly (default: 0.5)"
    )
    strategic_reports_parser.add_argument(
        "--distance-metric",
        type=str,
        default="spearman",
        help="Distance metric to use for similarity calculation (default: spearman). "
             "Available: spearman"
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
        help="Number of iterations for strategic reports. If provided, shows evolution over time. "
             "If not provided, shows single election outcome."
    )
    proportions_parser.add_argument(
        "--anchor",
        type=float,
        default=0.5,
        help="Anchor parameter (0-1) for strategic reports. Only used when --T is provided. "
             "1.0 = reports never change, 0.0 = reports can change completely randomly (default: 0.5)"
    )
    proportions_parser.add_argument(
        "--distance-metric",
        type=str,
        default="spearman",
        help="Distance metric for strategic reports. Only used when --T is provided. "
             "Available: spearman, kendall_tau (default: spearman)"
    )
    proportions_parser.add_argument(
        "--mechanism",
        type=str,
        default="pairwise_majority",
        help="Aggregation mechanism (default: pairwise_majority)"
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
    
    args = parser.parse_args()
    
    if args.command == 'rankings':
        # Build argument list for rankings CLI
        rankings_args = []
        if args.m is not None:
            rankings_args.extend(['--m', str(args.m)])
        if args.alphabetical:
            rankings_args.append('--alphabetical')
        if args.plot:
            rankings_args.append('--plot')
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
        strategic_reports_args.extend(['--T', str(args.T)])
        strategic_reports_args.extend(['--anchor', str(args.anchor)])
        strategic_reports_args.extend(['--distance-metric', args.distance_metric])
        if args.alphabetical:
            strategic_reports_args.append('--alphabetical')
        if args.plot:
            strategic_reports_args.append('--plot')
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
            proportions_args.extend(['--anchor', str(args.anchor)])
            proportions_args.extend(['--distance-metric', args.distance_metric])
        proportions_args.extend(['--mechanism', args.mechanism])
        if args.title is not None:
            proportions_args.extend(['--title', args.title])
        if args.show_integers:
            proportions_args.append('--show-integers')
        if args.plot:
            proportions_args.append('--plot')
        proportions_main(proportions_args)


if __name__ == "__main__":
    main()
