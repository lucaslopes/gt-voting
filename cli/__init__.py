"""CLI entry points for ranking tools."""

from cli.rankings_cli import main as rankings_main
from cli.honest_reports_cli import main as honest_reports_main

__all__ = ['rankings_main', 'honest_reports_main']
