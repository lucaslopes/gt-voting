"""Shared plotting utility functions."""

import numpy as np
import matplotlib.colors as mcolors
from core.rankings_core import candidate_labels


def prepare_labels(rankings, labels=None):
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


def create_rainbow_colormap(n_rankings):
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


def create_ranking_labels(rankings, labels, use_integers, show_integers=False):
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
