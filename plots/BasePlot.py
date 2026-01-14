"""Base class for all plotting functionality with centralized path management."""

import os
import numpy as np
import matplotlib.colors as mcolors
from pathlib import Path
from core.rankings_core import candidate_labels


class BasePlot:
    """
    Base class for all plot classes that provides centralized path management,
    standardized figure saving functionality, and shared plotting utilities.
    
    Attributes:
        images_path: Path to the images directory (default: "images/")
    """
    
    # Shared plotting configuration constants for consistent styling across plots
    PLOT_FIGSIZE = (12, 8)  # Figure size (width, height) in inches
    PLOT_TITLE_FONTSIZE = 21
    PLOT_TITLE_PAD = 20
    PLOT_AXIS_LABEL_FONTSIZE = 18
    PLOT_TICK_LABELSIZE = 15
    PLOT_LEGEND_FONTSIZE = 15  # Used for legends and colorbar labels
    PLOT_COLORBAR_TICK_LABELSIZE = 15
    
    def __init__(self, images_path="images/"):
        """
        Initialize BasePlot with images directory path.
        
        Args:
            images_path: Path to the images directory (default: "images/")
        """
        self.images_path = images_path
    
    def get_filepath(self, filename):
        """
        Get the full filepath by joining images_path with filename.
        
        Args:
            filename: Name of the file (without path)
            
        Returns:
            Full filepath as a string
        """
        return os.path.join(self.images_path, filename)
    
    def ensure_images_dir(self):
        """Create images directory if it doesn't exist."""
        os.makedirs(self.images_path, exist_ok=True)
    
    def save_figure(self, fig, filename, format='pdf', dpi=300, 
                    bbox_inches='tight', pad_inches=0.1):
        """
        Save figure to images directory.
        
        Args:
            fig: Matplotlib figure object to save
            filename: Name of the file (without path)
            format: File format (default: 'pdf')
            dpi: Resolution in dots per inch (default: 300)
            bbox_inches: Bounding box in inches (default: 'tight')
            pad_inches: Padding in inches (default: 0.1)
            
        Returns:
            Full filepath where the figure was saved
        """
        self.ensure_images_dir()
        filepath = self.get_filepath(filename)
        fig.savefig(
            filepath,
            format=format,
            dpi=dpi,
            bbox_inches=bbox_inches,
            pad_inches=pad_inches
        )
        return filepath
    
    def prepare_labels(self, rankings, labels=None):
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
    
    def create_rainbow_colormap(self, n_rankings):
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
    
    def create_ranking_labels(self, rankings, labels, use_integers, show_integers=False):
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
    
    def create_candidate_colormap(self, m):
        """
        Create a colormap for m candidates using distinct colors.
        
        Uses a rainbow-like progression from purple to red, similar to the ranking colormap
        but optimized for fewer categories (candidates).
        
        Args:
            m: Number of candidates
        
        Returns:
            List of hex color strings
        """
        if m == 1:
            return ['#6B4C93']  # Muted purple
        
        # Create colors from purple to red with good separation
        # Using HSV space: purple (0.75) → blue (0.67) → cyan (0.5) → green (0.33) → yellow (0.17) → red (0.0)
        hsv_values = np.linspace(0.75, 0.0, m)
        colors = [mcolors.hsv_to_rgb([h, 0.7, 0.85]) for h in hsv_values]  # Saturation=0.7, Value=0.85
        # Convert to hex format
        return [mcolors.rgb2hex(c) for c in colors]
