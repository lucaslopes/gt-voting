"""Ternary trajectory plot for visualizing voting dynamics."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize, LinearSegmentedColormap
from core.rankings_core import candidate_labels
from core.phase_transition import run_phase_transition_ternary
from plots.BasePlot import BasePlot


def _project_ternary(p_vec):
    """
    Project 3D probability vectors to 2D barycentric coordinates for ternary plot.
    
    Args:
        p_vec: Array of shape (T, 3) containing probability vectors
        
    Returns:
        Tuple (x, y) of projected coordinates
    """
    # p_vec shape (T, 3)
    # Vertices of triangle: (0,0), (1,0), (0.5, sqrt(3)/2)
    # Corresponds to p1=(1,0,0), p2=(0,1,0), p3=(0,0,1)
    # Mapping: A (top), B (right), C (left)
    # p[0] -> Top (0.5, sqrt(3)/2)
    # p[1] -> Right (1, 0)
    # p[2] -> Left (0, 0)
    
    x = 0.5 * p_vec[:, 0] + 1.0 * p_vec[:, 1] + 0.0 * p_vec[:, 2]
    y = (np.sqrt(3) / 2) * p_vec[:, 0] + 0.0 * p_vec[:, 1] + 0.0 * p_vec[:, 2]
    return x, y


def plot_single_ternary(ax, traj, p_initial_baseline=None, labels=None, title=None, 
                        show_instantaneous=True, show_running_avg=True, show_start=True, show_end=True,
                        instant_alpha=0.3, instant_lw=0.5, avg_lw=2, use_gradient=True, show_labels=True,
                        title_fontsize=None, label_fontsize=None, title_pad=None):
    """
    Plot a single ternary trajectory on the given axes.
    
    This is a reusable function that can be called from both plot_ternary.py and plot_dashboard.py
    to avoid code duplication.
    
    Args:
        ax: Matplotlib axes to plot on
        traj: Trajectory array of shape (T, 3) containing instantaneous outcomes
        p_initial_baseline: Optional initial baseline outcome (shape (3,)) to prepend to trajectories
        labels: Optional list of candidate labels (default: A, B, C)
        title: Optional title for the plot
        show_instantaneous: Whether to show instantaneous trajectory (default: True)
        show_running_avg: Whether to show running average trajectory (default: True)
        show_start: Whether to show start marker (default: True)
        show_end: Whether to show end marker (default: True)
        instant_alpha: Alpha transparency for instantaneous trajectory (default: 0.3)
        instant_lw: Line width for instantaneous trajectory (default: 0.5)
        avg_lw: Line width for running average (default: 2)
        use_gradient: Whether to use color gradient for running average (default: True)
        show_labels: Whether to show candidate labels at triangle vertices (default: True)
        title_fontsize: Font size for title (default: 12, or use BasePlot.PLOT_TITLE_FONTSIZE if available)
        label_fontsize: Font size for candidate labels (default: 12, or use BasePlot.PLOT_AXIS_LABEL_FONTSIZE if available)
    
    Returns:
        Tuple (handles, labels_legend) for legend
    """
    # Get default font sizes from BasePlot if available
    if title_fontsize is None:
        try:
            from plots.BasePlot import BasePlot
            title_fontsize = BasePlot.PLOT_TITLE_FONTSIZE
        except:
            title_fontsize = 12
    
    if label_fontsize is None:
        try:
            from plots.BasePlot import BasePlot
            label_fontsize = BasePlot.PLOT_AXIS_LABEL_FONTSIZE
        except:
            label_fontsize = 12
    if labels is None:
        from core.rankings_core import candidate_labels
        labels = candidate_labels(3)
    
    T = len(traj)
    
    # Prepend initial baseline to trajectory for running average computation
    if p_initial_baseline is not None:
        traj_with_initial = np.vstack([p_initial_baseline.reshape(1, -1), traj])
        T_with_initial = len(traj_with_initial)
        running_avg = np.cumsum(traj_with_initial, axis=0) / np.arange(1, T_with_initial + 1)[:, None]
    else:
        running_avg = np.cumsum(traj, axis=0) / np.arange(1, T + 1)[:, None]
    
    # Draw simplex triangle
    # Scale triangle to make it larger (scale factor > 1.0)
    scale_factor = 2.0  # Increase triangle size by 100% (double the size)
    tri_x_base = [0, 1, 0.5, 0]
    tri_y_base = [0, 0, np.sqrt(3) / 2, 0]
    # Center of triangle is at (0.5, sqrt(3)/6)
    center_x = 0.5
    center_y = np.sqrt(3) / 6
    # Scale around center
    tri_x = [(x - center_x) * scale_factor + center_x for x in tri_x_base]
    tri_y = [(y - center_y) * scale_factor + center_y for y in tri_y_base]
    ax.plot(tri_x, tri_y, "k-", lw=1.5)
    
    # Add candidate labels at triangle vertices (optional, for custom positioning)
    if show_labels:
        # Use scaled triangle vertices for label positioning
        ax.text(tri_x[2], tri_y[2] + 0.02, f"Cand {labels[0]}", ha="center", 
                fontsize=label_fontsize, va="bottom")
        ax.text(tri_x[1] + 0.02, tri_y[1] - 0.05, f"Cand {labels[1]}", ha="center", fontsize=label_fontsize, va="top")
        ax.text(tri_x[0] - 0.02, tri_y[0] - 0.05, f"Cand {labels[2]}", ha="center", fontsize=label_fontsize, va="top")
    
    # Prepend initial baseline to instantaneous trajectory so it starts from the X mark
    if p_initial_baseline is not None:
        traj_instant = np.vstack([p_initial_baseline.reshape(1, -1), traj])
    else:
        traj_instant = traj
    
    # Project trajectories
    inst_x, inst_y = _project_ternary(traj_instant)
    avg_x, avg_y = _project_ternary(running_avg)
    
    # Scale projected coordinates to match the scaled triangle border
    # Use the same scale_factor and center as the triangle
    inst_x = (inst_x - center_x) * scale_factor + center_x
    inst_y = (inst_y - center_y) * scale_factor + center_y
    avg_x = (avg_x - center_x) * scale_factor + center_x
    avg_y = (avg_y - center_y) * scale_factor + center_y
    
    handles = []
    labels_legend = []
    
    # Plot instantaneous trajectory
    if show_instantaneous:
        line_inst = ax.plot(inst_x, inst_y, "o-", c="gray", alpha=instant_alpha, 
                           markersize=2, linewidth=instant_lw, label="Instantaneous $p^t$")[0]
        handles.append(line_inst)
        labels_legend.append("Instantaneous $p^t$")
    
    # Plot running average
    if show_running_avg:
        if use_gradient:
            # Use colored gradient from start to finish
            points = np.array([avg_x, avg_y]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            traj_len = T_with_initial if p_initial_baseline is not None else T
            
            # Create a custom two-color gradient from warm (start) to cool (end)
            # Red/orange at start -> Blue/purple at end
            colors = ['#FF6B35', '#004E89']  # Orange-red to deep blue
            n_bins = 256
            cmap = LinearSegmentedColormap.from_list('trajectory_gradient', colors, N=n_bins)
            
            # Normalize from 0 (start) to traj_len - 1 (finish)
            # Each segment connects point i to point i+1, so we have traj_len - 1 segments
            # Color each segment at its midpoint to get smooth gradient from start to finish
            norm = Normalize(0, traj_len - 1)
            lc = LineCollection(segments, cmap=cmap, norm=norm)
            # Use midpoint indices: [0.5, 1.5, 2.5, ..., traj_len - 1.5]
            # This ensures the gradient smoothly transitions from start to finish
            segment_indices = np.arange(traj_len - 1) + 0.5
            lc.set_array(segment_indices)
            lc.set_linewidth(avg_lw)
            ax.add_collection(lc)
            # Create a proxy artist for legend
            from matplotlib.lines import Line2D
            proxy = Line2D([0], [0], color='blue', linewidth=avg_lw)
            handles.append(proxy)
            labels_legend.append("Running Avg")
        else:
            # Use solid line
            line_avg = ax.plot(avg_x, avg_y, "b-", lw=avg_lw, label="Running Avg")[0]
            handles.append(line_avg)
            labels_legend.append("Running Avg")
    
    # Mark start and end
    if show_start:
        if p_initial_baseline is not None:
            start_x, start_y = _project_ternary(p_initial_baseline.reshape(1, -1))
            # Scale to match the scaled triangle
            start_x = (start_x - center_x) * scale_factor + center_x
            start_y = (start_y - center_y) * scale_factor + center_y
            marker_start = ax.scatter(start_x[0], start_y[0], c="red", marker="x", 
                                     s=100, label="Start", zorder=10)
        else:
            marker_start = ax.scatter(avg_x[0], avg_y[0], c="red", marker="x", 
                                     s=100, label="Start", zorder=10)
        handles.append(marker_start)
        labels_legend.append("Start")
    
    if show_end:
        marker_end = ax.scatter(avg_x[-1], avg_y[-1], c="blue", marker="*", 
                               s=150, label="End (Avg)", zorder=10)
        handles.append(marker_end)
        labels_legend.append("End (Avg)")
    
    if title:
        ax.set_title(title, fontsize=title_fontsize, fontweight='bold')
    ax.axis("off")
    ax.set_aspect("equal")
    
    return handles, labels_legend


class TernaryPlot(BasePlot):
    """Ternary trajectory plot for visualizing voting dynamics."""
    
    def plot(self, n=15, m=3, eta=0.2, beta=3.0, T=300, seed=0, baselines=None,
             ax=None, title=None, alpha=None, alpha_before=None, alpha_after=None, ternary_data=None):
        """
        Plot ternary trajectory plot(s) for given alpha value(s).
        
        Args:
            n: Number of voters (default: 15)
            m: Number of candidates (must be 3, raises ValueError otherwise)
            eta: Learning rate parameter (default: 0.2)
            beta: Temperature/sharpness parameter (default: 3.0)
            T: Number of time steps (default: 300)
            seed: Random seed (default: 0)
            baselines: Optional baseline permutation indices
            ax: Optional matplotlib axes (if None, creates new figure)
            title: Optional title for the plot
            alpha: Single alpha value for a single plot (0-1)
            alpha_before: Alpha value for "before threshold" plot (0-1). Requires alpha_after for two plots.
            alpha_after: Alpha value for "after threshold" plot (0-1). Requires alpha_before for two plots.
            
        Returns:
            The matplotlib figure object containing the plot(s)
            
        Raises:
            ValueError: If m != 3, or if alpha arguments are invalid
        """
        if m != 3:
            raise ValueError("Ternary plot requires m == 3")
        
        # Determine plot mode: single plot or two plots
        if alpha_before is not None and alpha_after is not None:
            # Two plots mode
            alphas = [alpha_before, alpha_after]
            labels = [
                f"Before Threshold\n($\\alpha={alpha_before:.3f}$)",
                f"After Threshold\n($\\alpha={alpha_after:.3f}$)"
            ]
            n_plots = 2
        elif alpha is not None:
            # Single plot mode
            alphas = [alpha]
            labels = [f"Ternary Plot ($\\alpha={alpha:.3f}$)"]
            n_plots = 1
        else:
            raise ValueError(
                "Must provide either --anchor-strength (or --alpha) for a single plot, "
                "or both --alpha-before and --alpha-after for two plots"
            )
        
        # Generate trajectories for all scenarios (or use cached data)
        if ternary_data is not None:
            trajectories = ternary_data.get("trajectories")
            if trajectories is None:
                raise ValueError("ternary_data must include 'trajectories'")
            if len(trajectories) != len(alphas):
                raise ValueError("ternary_data trajectories length does not match requested alphas")
        else:
            trajectories = []
            for a in alphas:
                traj = run_phase_transition_ternary(
                    a, T=T, n=n, m=m, eta=eta, beta=beta, seed=seed, baselines=baselines
                )
                trajectories.append(traj)
        
        # Create figure if needed
        if ax is None:
            fig, axes = plt.subplots(1, n_plots, figsize=(7 * n_plots, 6))
            if n_plots == 1:
                axes = [axes]  # Make it iterable
        else:
            # If ax is provided, assume it's a single axes and create subplots
            fig = ax.figure
            fig.clear()
            axes = fig.subplots(1, n_plots)
            if n_plots == 1:
                axes = [axes]
        
        # Get candidate labels
        labels_candidates = candidate_labels(m)
        
        # Compute initial baseline outcome if baselines are provided
        p_initial_baseline = None
        if baselines is not None:
            from core.aggregator_core import aggregate_rankings, reorder_probabilities
            from core.honest_reports import baseline_indices_to_rankings
            initial_rankings = baseline_indices_to_rankings(baselines, m)
            probabilities = aggregate_rankings(initial_rankings)
            p_initial_baseline = np.array(
                reorder_probabilities(probabilities, initial_rankings[0], range(m))
            )
        
        # Plot each scenario using the reusable helper function
        handles_all = None
        labels_all = None
        for idx, (a, traj, label) in enumerate(zip(alphas, trajectories, labels)):
            ax = axes[idx]
            
            handles, labels_legend = plot_single_ternary(
                ax,
                traj,
                p_initial_baseline=p_initial_baseline,
                labels=labels_candidates,
                title=label,
                show_instantaneous=True,
                show_running_avg=True,
                show_start=True,
                show_end=True,
                instant_alpha=0.2,
                instant_lw=0.5,
                avg_lw=2.5,
                use_gradient=True,  # Use gradient for standalone ternary plots
                title_fontsize=self.PLOT_TITLE_FONTSIZE,  # Use BasePlot font size
                label_fontsize=self.PLOT_AXIS_LABEL_FONTSIZE  # Use BasePlot font size
            )
            
            # Store handles and labels from first plot for legend
            if idx == 0:
                handles_all = handles
                labels_all = labels_legend
                ax.legend(handles, labels_legend, loc="upper right", fontsize=self.PLOT_LEGEND_FONTSIZE)
        
        # Add overall suptitle
        if title is None:
            if n_plots == 1:
                title = "Dynamics of the GT Outcome:\nInstantaneous vs Running Average"
            else:
                title = "Dynamics of the GT Outcome:\nInstantaneous vs Running Average"
        plt.suptitle(title, fontsize=self.PLOT_TITLE_FONTSIZE)
        plt.tight_layout()
        
        return fig


# Backward compatibility wrapper
def plot_ternary_trajectories(*args, **kwargs):
    """Backward compatibility wrapper for plot_ternary_trajectories function."""
    plotter = TernaryPlot()
    return plotter.plot(*args, **kwargs)
