"""Plotting utilities for voting system visualizations."""

from plots.BasePlot import BasePlot
from plots.plot_rankings import plot_rankings_list
from plots.plot_voter_strategies import plot_voter_strategies
from plots.plot_ternary import plot_ternary_trajectories

# Create a singleton instance for backward compatibility function exports
_plot_instance = BasePlot()

# Export constants from BasePlot class
PLOT_FIGSIZE = BasePlot.PLOT_FIGSIZE
PLOT_TITLE_FONTSIZE = BasePlot.PLOT_TITLE_FONTSIZE
PLOT_TITLE_PAD = BasePlot.PLOT_TITLE_PAD
PLOT_AXIS_LABEL_FONTSIZE = BasePlot.PLOT_AXIS_LABEL_FONTSIZE
PLOT_TICK_LABELSIZE = BasePlot.PLOT_TICK_LABELSIZE
PLOT_LEGEND_FONTSIZE = BasePlot.PLOT_LEGEND_FONTSIZE
PLOT_COLORBAR_TICK_LABELSIZE = BasePlot.PLOT_COLORBAR_TICK_LABELSIZE


def prepare_labels(rankings, labels=None):
    """
    Determine if rankings are integer or string tuples and prepare labels.
    
    Backward compatibility wrapper for BasePlot.prepare_labels().
    
    Args:
        rankings: List of ranking tuples
        labels: Optional list of candidate labels
    
    Returns:
        Tuple (use_integers, labels) where use_integers is bool and labels is list
    """
    return _plot_instance.prepare_labels(rankings, labels)


def create_rainbow_colormap(n_rankings):
    """
    Create a rainbow colormap from purple to red with muted tones.
    
    Backward compatibility wrapper for BasePlot.create_rainbow_colormap().
    
    Args:
        n_rankings: Number of rankings (determines number of colors)
    
    Returns:
        List of hex color strings
    """
    return _plot_instance.create_rainbow_colormap(n_rankings)


def create_ranking_labels(rankings, labels, use_integers, show_integers=False):
    """
    Create ranking labels in "A>B>C" or "0>1>2" format.
    
    Backward compatibility wrapper for BasePlot.create_ranking_labels().
    
    Args:
        rankings: List of ranking tuples
        labels: List of candidate labels
        use_integers: Whether rankings contain integer indices
        show_integers: If True and use_integers is True, show integers instead of converting to labels
    
    Returns:
        List of ranking label strings
    """
    return _plot_instance.create_ranking_labels(rankings, labels, use_integers, show_integers)


__all__ = [
    'BasePlot',
    'plot_rankings_list',
    'plot_voter_strategies',
    'plot_ternary_trajectories',
    'prepare_labels',
    'create_rainbow_colormap',
    'create_ranking_labels',
    'PLOT_FIGSIZE',
    'PLOT_TITLE_FONTSIZE',
    'PLOT_TITLE_PAD',
    'PLOT_AXIS_LABEL_FONTSIZE',
    'PLOT_TICK_LABELSIZE',
    'PLOT_LEGEND_FONTSIZE',
    'PLOT_COLORBAR_TICK_LABELSIZE',
]
