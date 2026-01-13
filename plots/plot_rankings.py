import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from math import ceil, sqrt
from plots.plot_utils import prepare_labels, create_rainbow_colormap, create_ranking_labels


def _determine_layout(layout, n_rankings):
    """
    Determine the actual layout (resolves 'auto' to a specific layout).
    
    Args:
        layout: Layout style ('horizontal', 'vertical', 'matrix', or 'auto')
        n_rankings: Number of rankings
    
    Returns:
        Resolved layout string
    """
    if layout == 'auto':
        if n_rankings <= 6:
            return 'horizontal'
        elif n_rankings <= 24:
            return 'matrix'
        else:
            return 'vertical'
    return layout


def _calculate_grid_dimensions(layout, n_rankings):
    """
    Calculate grid dimensions (rows and columns) based on layout.
    
    Args:
        layout: Layout style ('horizontal', 'vertical', or 'matrix')
        n_rankings: Number of rankings
    
    Returns:
        Tuple (n_rows, n_cols)
    """
    if layout == 'horizontal':
        return 1, n_rankings
    elif layout == 'vertical':
        return n_rankings, 1
    else:  # matrix
        n_cols = min(6, ceil(sqrt(n_rankings)))  # Max 6 columns, or sqrt for square-ish grid
        n_rows = ceil(n_rankings / n_cols)
        return n_rows, n_cols


def _create_heatmap_data(n_rankings, n_rows, n_cols):
    """
    Create data array for heatmap where each cell contains the ranking index.
    Unused cells are set to NaN.
    
    Args:
        n_rankings: Number of rankings
        n_rows: Number of rows in grid
        n_cols: Number of columns in grid
    
    Returns:
        numpy array of shape (n_rows, n_cols) with ranking indices or NaN
    """
    data = np.full((n_rows, n_cols), np.nan, dtype=float)
    for idx in range(n_rankings):
        row = idx // n_cols
        col = idx % n_cols
        if row < n_rows and col < n_cols:
            data[row, col] = idx
    return data


def _create_colormap_and_norm(colors_rainbow, n_rankings):
    """
    Create matplotlib colormap and normalization for the heatmap.
    
    Args:
        colors_rainbow: List of hex color strings
        n_rankings: Number of rankings
    
    Returns:
        Tuple (cmap, norm) where cmap is ListedColormap and norm is BoundaryNorm
    """
    cmap = mcolors.ListedColormap(colors_rainbow)
    # Set background color for NaN values (unused cells)
    cmap.set_bad(color='#F5F5F5', alpha=1.0)  # Light gray background for unused cells
    bounds = np.arange(n_rankings + 1) - 0.5
    norm = mcolors.BoundaryNorm(bounds, n_rankings)
    return cmap, norm


def _add_cell_labels(ax, rankings, perm_labels, n_rows, n_cols):
    """
    Add text labels to each cell in the heatmap.
    
    Args:
        ax: Matplotlib axes object
        rankings: List of ranking tuples
        perm_labels: List of ranking label strings
        n_rows: Number of rows in grid
        n_cols: Number of columns in grid
    """
    for idx in range(len(rankings)):
        row = idx // n_cols
        col = idx % n_cols
        if row < n_rows and col < n_cols:
            ax.text(col, row, perm_labels[idx], ha='center', va='center', 
                   fontsize=14, fontweight='bold', color='white')


def _configure_axes(ax, n_rows, n_cols, n_candidates, n_rankings):
    """
    Configure axes ticks, labels, and title.
    
    Args:
        ax: Matplotlib axes object
        n_rows: Number of rows in grid
        n_cols: Number of columns in grid
        n_candidates: Number of candidates
        n_rankings: Number of rankings
    """
    ax.set_xticks(range(n_cols))
    ax.set_yticks(range(n_rows))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_title(f"All Possible Rankings for {n_candidates} Candidates (Total: {n_rankings})", 
                 fontsize=21, fontweight='bold', pad=20)


def _add_colorbar(im, ax, perm_labels, n_rankings):
    """
    Add colorbar legend to the plot.
    
    Args:
        im: Matplotlib image object from imshow
        ax: Matplotlib axes object
        perm_labels: List of ranking label strings
        n_rankings: Number of rankings
    
    Returns:
        Colorbar object
    """
    tick_locs = np.arange(n_rankings)
    bounds = np.arange(n_rankings + 1) - 0.5
    cbar = plt.colorbar(im, ax=ax, ticks=tick_locs, boundaries=bounds)
    cbar.ax.set_yticklabels(perm_labels, fontsize=15)
    cbar.ax.invert_yaxis()  # Put first ranking at top
    cbar.set_label("Reported Ranking", fontsize=17)
    return cbar


def plot_rankings_list(rankings, labels=None, layout='auto', ax=None, show_integers=False):
    """
    Plot all possible rankings as a heatmap where each cell represents one ranking.
    Each cell is colored according to the ranking's position in the rainbow colormap.
    
    Args:
        rankings: List of ranking tuples (either integer tuples or string tuples)
        labels: Optional list of candidate labels. If None and rankings contain integers,
                will generate labels automatically using A, B, C, etc.
        layout: Layout style - 'horizontal', 'vertical', 'matrix', or 'auto' (default).
                'auto' chooses based on number of rankings:
                - <= 6: horizontal
                - 7-24: matrix (square-ish)
                - > 24: vertical
        ax: Optional matplotlib axes. If None, creates a new figure.
        show_integers: If True and rankings contain integers, display them as integers
                      (e.g., "0>1>2") instead of converting to labels (e.g., "A>B>C")
    
    Returns:
        The matplotlib axes object containing the plot
    """
    # Initialize figure if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    
    n_rankings = len(rankings)
    if n_rankings == 0:
        ax.text(0.5, 0.5, "No rankings to display", ha='center', va='center', fontsize=21)
        ax.axis('off')
        return ax
    
    # Prepare labels and determine data type
    use_integers, labels = prepare_labels(rankings, labels)
    
    # Create rainbow colormap
    colors_rainbow = create_rainbow_colormap(n_rankings)
    
    # Create ranking labels (e.g., "A>B>C" or "0>1>2" depending on show_integers)
    perm_labels = create_ranking_labels(rankings, labels, use_integers, show_integers)
    
    # Determine layout and calculate grid dimensions
    resolved_layout = _determine_layout(layout, n_rankings)
    n_rows, n_cols = _calculate_grid_dimensions(resolved_layout, n_rankings)
    
    # Create heatmap data array
    data = _create_heatmap_data(n_rankings, n_rows, n_cols)
    
    # Create colormap and normalization
    cmap, norm = _create_colormap_and_norm(colors_rainbow, n_rankings)
    
    # Plot heatmap
    im = ax.imshow(data, aspect='auto', cmap=cmap, norm=norm, interpolation='nearest')
    
    # Add cell labels
    _add_cell_labels(ax, rankings, perm_labels, n_rows, n_cols)
    
    # Configure axes
    _configure_axes(ax, n_rows, n_cols, len(labels), n_rankings)
    
    # Add colorbar
    _add_colorbar(im, ax, perm_labels, n_rankings)
    
    return ax
