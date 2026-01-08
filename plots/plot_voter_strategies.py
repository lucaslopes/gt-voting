"""Plot voter strategy evolution as a heatmap where each cell represents a voter's ranking at a time step."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from plots.plot_utils import prepare_labels, create_rainbow_colormap, create_ranking_labels


def plot_voter_strategies(strategies, rankings, labels=None, ax=None, show_integers=False, title=None):
    """
    Plot voter strategy evolution as a heatmap.
    
    Each cell in the heatmap represents a voter's ranking at a specific time step.
    The color of each cell corresponds to the ranking index from the list of all possible rankings.
    
    Args:
        strategies: Array of shape [n, T] where each value is a ranking index.
                    strategies[i, t] is the ranking index that voter i is using at time t.
        rankings: List of all possible ranking tuples (same format as generate_rankings output).
                  Used to create labels and validate indices.
        labels: Optional list of candidate labels. If None and rankings contain integers,
                will generate labels automatically using A, B, C, etc.
        ax: Optional matplotlib axes. If None, creates a new figure.
        show_integers: If True and rankings contain integers, display them as integers
                      (e.g., "0>1>2") instead of converting to labels (e.g., "A>B>C")
        title: Optional title for the plot. If None, uses default title.
    
    Returns:
        The matplotlib axes object containing the plot
    """
    # Initialize figure if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    
    # Validate input shapes
    if strategies.ndim != 2:
        raise ValueError(f"strategies must be 2D array [n, T], got shape {strategies.shape}")
    
    n_voters, n_timesteps = strategies.shape
    n_rankings = len(rankings)
    
    if n_rankings == 0:
        ax.text(0.5, 0.5, "No rankings provided", ha='center', va='center', fontsize=14)
        ax.axis('off')
        return ax
    
    # Validate that strategy indices are within valid range
    max_idx = np.max(strategies)
    min_idx = np.min(strategies)
    if min_idx < 0 or max_idx >= n_rankings:
        raise ValueError(f"Strategy indices must be in range [0, {n_rankings-1}], "
                        f"got range [{min_idx}, {max_idx}]")
    
    # Prepare labels and determine data type
    use_integers, labels = prepare_labels(rankings, labels)
    
    # Create rainbow colormap
    colors_rainbow = create_rainbow_colormap(n_rankings)
    
    # Create ranking labels (e.g., "A>B>C" or "0>1>2" depending on show_integers)
    perm_labels = create_ranking_labels(rankings, labels, use_integers, show_integers)
    
    # Create colormap and normalization
    cmap = mcolors.ListedColormap(colors_rainbow)
    bounds = np.arange(n_rankings + 1) - 0.5
    norm = mcolors.BoundaryNorm(bounds, n_rankings)
    
    # Plot heatmap
    im = ax.imshow(
        strategies,
        aspect='auto',
        cmap=cmap,
        norm=norm,
        interpolation='nearest',
    )
    
    # Configure axes
    ax.set_xlabel("Time Step (t)", fontsize=12)
    ax.set_ylabel("Voter Index", fontsize=12)
    ax.set_yticks(range(n_voters))
    
    # Set title
    if title is None:
        ax.set_title(f"Voter Strategy Evolution ({n_voters} voters, {n_timesteps} time steps)", 
                    fontsize=14, fontweight='bold', pad=20)
    else:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add colorbar
    tick_locs = np.arange(n_rankings)
    cbar = plt.colorbar(im, ax=ax, ticks=tick_locs, boundaries=bounds)
    cbar.ax.set_yticklabels(perm_labels)
    cbar.ax.invert_yaxis()  # Put the first ranking at the top
    cbar.set_label("Reported Ranking", fontsize=11)
    
    return ax
