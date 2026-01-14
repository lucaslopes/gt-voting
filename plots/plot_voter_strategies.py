"""Plot voter strategy evolution as a heatmap where each cell represents a voter's ranking at a time step."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from plots.BasePlot import BasePlot


class VoterStrategiesPlot(BasePlot):
    """Plot voter strategy evolution as a heatmap."""
    
    def plot(self, strategies, rankings, labels=None, ax=None, show_integers=False,
             title=None, probs=None, title_fontsize=None):
        """
        Plot voter strategy evolution as a heatmap.
        
        Each cell in the heatmap represents a voter's ranking at a specific time step.
        The hue of each cell corresponds to the ranking index from the list of all
        possible rankings. When a probability matrix is provided via `probs`, the
        saturation of the color is modulated per cell so that higher probability
        rankings appear more saturated and lower probability rankings appear more
        washed out.
        
        Args:
            strategies: Array of shape [voters, T] where each value is a ranking index.
                        strategies[i, t] is the ranking index that voter i is using at time t.
            rankings: List of all possible ranking tuples (same format as generate_rankings output).
                      Used to create labels and validate indices.
            labels: Optional list of candidate labels. If None and rankings contain integers,
                    will generate labels automatically using A, B, C, etc.
            ax: Optional matplotlib axes. If None, creates a new figure.
            show_integers: If True and rankings contain integers, display them as integers
                          (e.g., "0>1>2") instead of converting to labels (e.g., "A>B>C")
            title: Optional title for the plot. If None, uses default title.
            probs: Optional numpy array of shape [voters, T] with values in [0, 1].
                   probs[i, t] gives the probability mass assigned to the selected
                   ranking for voter i at time t. If provided, it is used to scale
                   the saturation channel of each cell's color; if None, full
                   saturation is used everywhere.
            title_fontsize: Optional font size for the title. If None, uses PLOT_TITLE_FONTSIZE.
        
        Returns:
            The matplotlib axes object containing the plot
        """
        # Initialize figure if needed
        if ax is None:
            fig, ax = plt.subplots(figsize=self.PLOT_FIGSIZE)
        
        # Validate input shapes
        if strategies.ndim != 2:
            raise ValueError(f"strategies must be 2D array [voters, T], got shape {strategies.shape}")
        
        n_voters, n_timesteps = strategies.shape
        n_rankings = len(rankings)
        
        if n_rankings == 0:
            ax.text(0.5, 0.5, "No rankings provided", ha='center', va='center', fontsize=self.PLOT_TITLE_FONTSIZE)
            ax.axis('off')
            return ax
        
        # Validate that strategy indices are within valid range
        max_idx = np.max(strategies)
        min_idx = np.min(strategies)
        if min_idx < 0 or max_idx >= n_rankings:
            raise ValueError(f"Strategy indices must be in range [0, {n_rankings-1}], "
                            f"got range [{min_idx}, {max_idx}]")
        
        # Prepare labels and determine data type
        use_integers, labels = self.prepare_labels(rankings, labels)
        
        # Create rainbow colormap
        colors_rainbow = self.create_rainbow_colormap(n_rankings)
        
        # Create ranking labels (e.g., "A>B>C" or "0>1>2" depending on show_integers)
        perm_labels = self.create_ranking_labels(rankings, labels, use_integers, show_integers)
        
        # Create colormap and normalization
        cmap = mcolors.ListedColormap(colors_rainbow)
        bounds = np.arange(n_rankings + 1) - 0.5
        norm = mcolors.BoundaryNorm(bounds, n_rankings)

        # Map strategies (ranking indices) to RGBA colors
        rgba = cmap(norm(strategies))

        # Optionally modulate saturation based on provided probabilities
        if probs is not None:
            if probs.shape != strategies.shape:
                raise ValueError(
                    f"probs must have same shape as strategies ({strategies.shape}), "
                    f"got {probs.shape}"
                )

            # Clip probabilities to [0, 1] and replace NaNs with 0
            probs_clipped = np.clip(probs.astype(float), 0.0, 1.0)
            probs_clipped = np.nan_to_num(probs_clipped, nan=0.0)

            # Convert RGB to HSV, scale saturation by probabilities, then convert back
            rgb = rgba[..., :3]
            hsv = mcolors.rgb_to_hsv(rgb)

            # Scale saturation channel
            hsv[..., 1] *= probs_clipped

            # Ensure saturation remains within [0, 1]
            hsv[..., 1] = np.clip(hsv[..., 1], 0.0, 1.0)

            rgb_modulated = mcolors.hsv_to_hsv(hsv) if hasattr(mcolors, "hsv_to_hsv") else mcolors.hsv_to_rgb(hsv)
            rgba[..., :3] = rgb_modulated

        # Plot heatmap using the RGBA image
        im = ax.imshow(
            rgba,
            aspect='auto',
            interpolation='nearest',
        )
        
        # Configure axes
        ax.set_xlabel("Time Step (t)", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax.set_ylabel("Voter Index", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax.set_yticks(range(n_voters))
        
        # Set x-axis ticks with evenly spaced labels to avoid overlap
        # Use a reasonable number of ticks (5-10) based on the number of time steps
        # Always include t=0 and t=T-1
        if n_timesteps <= 10:
            # For small numbers, show all ticks
            x_ticks = list(range(n_timesteps))
        else:
            # For larger numbers, use 6-8 evenly spaced ticks
            n_ticks = min(8, max(6, n_timesteps // 50))
            # Generate evenly spaced tick positions
            x_ticks = np.linspace(0, n_timesteps - 1, n_ticks, dtype=int)
            # Ensure we have t=0 and t=T-1
            if x_ticks[0] != 0:
                x_ticks[0] = 0
            if x_ticks[-1] != n_timesteps - 1:
                x_ticks[-1] = n_timesteps - 1
            # Remove duplicates while preserving order
            x_ticks = list(dict.fromkeys(x_ticks))
        
        ax.set_xticks(x_ticks)
        ax.tick_params(axis='both', which='major', labelsize=self.PLOT_TICK_LABELSIZE)
        
        # Set title
        title_fs = title_fontsize if title_fontsize is not None else self.PLOT_TITLE_FONTSIZE
        if title is None:
            ax.set_title(f"Voter Strategy Evolution ({n_voters} voters, {n_timesteps} total number of time steps)", 
                        fontsize=title_fs, fontweight='bold', pad=self.PLOT_TITLE_PAD)
        else:
            ax.set_title(title, fontsize=title_fs, fontweight='bold', pad=self.PLOT_TITLE_PAD)
        
        # Add colorbar using a scalar mappable so that the colorbar reflects
        # the ranking index → hue mapping, independent of per-cell saturation
        tick_locs = np.arange(n_rankings)
        mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
        mappable.set_array([])
        cbar = plt.colorbar(mappable, ax=ax, ticks=tick_locs, boundaries=bounds)
        cbar.ax.set_yticklabels(perm_labels, fontsize=self.PLOT_COLORBAR_TICK_LABELSIZE)
        cbar.ax.invert_yaxis()  # Put the first ranking at the top
        cbar.set_label("Reported Ranking", fontsize=self.PLOT_LEGEND_FONTSIZE)
    
        # Adjust layout to ensure consistent spacing
        fig = ax.figure
        fig.tight_layout()
        
        return ax


# Backward compatibility wrapper
def plot_voter_strategies(*args, **kwargs):
    """Backward compatibility wrapper for plot_voter_strategies function."""
    plotter = VoterStrategiesPlot()
    return plotter.plot(*args, **kwargs)
