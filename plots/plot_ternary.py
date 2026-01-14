"""Ternary trajectory plot for visualizing voting dynamics."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
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


class TernaryPlot(BasePlot):
    """Ternary trajectory plot for visualizing voting dynamics."""
    
    def plot(self, n=15, m=3, eta=0.2, beta=3.0, T=300, seed=0, baselines=None,
             ax=None, title=None, alpha=None, alpha_before=None, alpha_after=None):
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
        
        # Generate trajectories for all scenarios
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
        
        # Plot each scenario
        for idx, (a, traj, label) in enumerate(zip(alphas, trajectories, labels)):
            ax = axes[idx]
            
            # Calculate running average
            running_avg = np.cumsum(traj, axis=0) / np.arange(1, T + 1)[:, None]
            
            # Draw simplex triangle
            tri_x = [0, 1, 0.5, 0]
            tri_y = [0, 0, np.sqrt(3) / 2, 0]
            ax.plot(tri_x, tri_y, "k-", lw=1.5)
            
            # Add candidate labels at triangle vertices
            ax.text(0.5, np.sqrt(3) / 2 + 0.02, f"Cand {labels_candidates[0]}", ha="center", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
            ax.text(1.02, -0.05, f"Cand {labels_candidates[1]}", ha="center", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
            ax.text(-0.02, -0.05, f"Cand {labels_candidates[2]}", ha="center", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
            
            # Project trajectories
            inst_x, inst_y = _project_ternary(traj)
            avg_x, avg_y = _project_ternary(running_avg)
            
            # Plot instantaneous trajectory (gray, faint)
            ax.plot(inst_x, inst_y, "o-", c="gray", alpha=0.2, markersize=2, label="Instantaneous $p^t$")
            
            # Plot running average with colored gradient
            points = np.array([avg_x, avg_y]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            
            norm = Normalize(0, T)
            lc = LineCollection(segments, cmap="viridis", norm=norm)
            lc.set_array(np.arange(T))
            lc.set_linewidth(2.5)
            ax.add_collection(lc)
            
            # Mark start and end
            ax.scatter(avg_x[0], avg_y[0], c="red", marker="x", s=100, label="Start", zorder=10)
            ax.scatter(avg_x[-1], avg_y[-1], c="blue", marker="*", s=150, label="End (Avg)", zorder=10)
            
            ax.set_title(label, fontsize=self.PLOT_TITLE_FONTSIZE)
            ax.axis("off")
            ax.set_aspect("equal")
            
            # Add legend only to first plot
            if idx == 0:
                ax.legend(loc="upper right", fontsize=self.PLOT_LEGEND_FONTSIZE)
        
        # Add overall suptitle
        if title is None:
            if n_plots == 1:
                title = "Dynamics of GT Voting Outcome:\nInstantaneous vs Running Average"
            else:
                title = "Dynamics of GT Voting Outcome:\nInstantaneous vs Running Average"
        plt.suptitle(title, fontsize=self.PLOT_TITLE_FONTSIZE)
        plt.tight_layout()
        
        return fig


# Backward compatibility wrapper
def plot_ternary_trajectories(*args, **kwargs):
    """Backward compatibility wrapper for plot_ternary_trajectories function."""
    plotter = TernaryPlot()
    return plotter.plot(*args, **kwargs)
