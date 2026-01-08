"""Plot voter strategy evolution as a heatmap where each cell represents a voter's ranking at a time step."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from core.rankings_core import candidate_labels


def _prepare_labels(rankings, labels=None):
    """
    Determine if rankings are integer or string tuples and prepare labels.
    
    Args:
        rankings: List of ranking tuples
        labels: Optional list of candidate labels
    
    Returns:
        Tuple (use_integers, labels) where use_integers is bool and labels is list
    """
    if isinstance(rankings[0][0], int):
        use_integers = True
        if labels is None:
            # Generate labels using the shared candidate_labels function
            max_candidate = max(max(r) for r in rankings)
            labels = candidate_labels(max_candidate + 1)
    else:
        use_integers = False
        if labels is None:
            # Extract unique labels from rankings
            all_labels = set()
            for r in rankings:
                all_labels.update(r)
            labels = sorted(list(all_labels))
    
    return use_integers, labels


def _create_rainbow_colormap(n_rankings):
    """
    Create a rainbow colormap from purple to red with muted tones.
    
    Args:
        n_rankings: Number of rankings (determines number of colors)
    
    Returns:
        List of hex color strings
    """
    if n_rankings == 1:
        return ['#6B4C93']  # Muted purple/violet
    
    # Create a custom colormap from purple to red with muted colors
    # Using HSV space: purple (0.75) → blue (0.67) → cyan (0.5) → green (0.33) → yellow (0.17) → red (0.0)
    # Reduced saturation (0.7) and brightness (0.85) for softer, more comfortable colors
    hsv_values = np.linspace(0.75, 0.0, n_rankings)  # From purple (0.75) to red (0.0)
    colors_rainbow = [mcolors.hsv_to_rgb([h, 0.7, 0.85]) for h in hsv_values]  # Saturation=0.7, Value=0.85
    # Convert to hex format
    return [mcolors.rgb2hex(c) for c in colors_rainbow]


def _create_ranking_labels(rankings, labels, use_integers, show_integers=False):
    """
    Create ranking labels in "A>B>C" or "0>1>2" format.
    
    Args:
        rankings: List of ranking tuples
        labels: List of candidate labels
        use_integers: Whether rankings contain integer indices
        show_integers: If True and use_integers is True, show integers instead of converting to labels
    
    Returns:
        List of ranking label strings
    """
    perm_labels = []
    for ranking in rankings:
        if use_integers and not show_integers:
            # Convert integers to alphabetical labels
            perm_labels.append(">".join(labels[c] for c in ranking))
        else:
            # Show as-is (integers as integers, strings as strings)
            perm_labels.append(">".join(str(c) for c in ranking))
    return perm_labels


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
    use_integers, labels = _prepare_labels(rankings, labels)
    
    # Create rainbow colormap
    colors_rainbow = _create_rainbow_colormap(n_rankings)
    
    # Create ranking labels (e.g., "A>B>C" or "0>1>2" depending on show_integers)
    perm_labels = _create_ranking_labels(rankings, labels, use_integers, show_integers)
    
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
