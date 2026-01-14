"""Phase transition plot with confidence intervals."""

import numpy as np
import matplotlib.pyplot as plt
from core.phase_transition import (
    run_phase_transition,
    compute_threshold_alpha,
    warp_alpha_axis,
)
from plots.BasePlot import BasePlot


class PhaseTransitionPlot(BasePlot):
    """Phase transition plot with confidence intervals."""
    
    def plot(self, n=15, m=3, eta=0.2, beta=3.0, seed=0, baselines=None,
             alpha_grid=None, ax=None, title=None, burn_in=200,
             collection_steps=50, runs=10, phase_data=None):
        """
        Plot phase transition: distance from center (tie) vs anchoring parameter (α) with confidence intervals.
        
        Args:
            n: Number of voters (default: 15)
            m: Number of candidates (default: 3)
            eta: Learning rate parameter (default: 0.2)
            beta: Temperature/sharpness parameter (default: 3.0)
            seed: Random seed (default: 0)
            baselines: Optional baseline permutation indices
            alpha_grid: Optional alpha grid for phase transition (if None, uses adaptive grid)
            ax: Optional matplotlib axes (if None, creates new figure)
            title: Optional title for the plot
            burn_in: Number of burn-in steps before collection (default: 200)
            collection_steps: Number of steps to collect and average (default: 50)
            runs: Number of independent runs per alpha value (default: 10)
            
        Returns:
            The matplotlib figure object containing the plot
        """
        # Run phase transition experiment (or use cached data)
        if phase_data is not None:
            alphas = phase_data["alphas"]
            dists_mean = phase_data["dists_mean"]
            dists_std = phase_data.get("dists_std")
            if dists_std is None:
                # Ensure std exists (e.g., single-run caches)
                dists_std = np.zeros_like(dists_mean, dtype=float)
            threshold_alpha = phase_data.get("threshold_alpha")
            if threshold_alpha is None:
                threshold_alpha = compute_threshold_alpha(alphas, dists_mean)
        else:
            alphas, dists_mean, dists_std = run_phase_transition(
                n=n, m=m, alpha_grid=alpha_grid, eta=eta, beta=beta, seed=seed, 
                baselines=baselines, burn_in=burn_in, collection_steps=collection_steps, runs=runs
            )
            threshold_alpha = compute_threshold_alpha(alphas, dists_mean)
        
        # Create figure if needed
        if ax is None:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        else:
            fig = ax.figure
        
        # Apply nonlinear transform to stretch x-axis near threshold
        warp_power = 0.4  # Power parameter: lower values = more stretching near threshold
        if threshold_alpha is not None:
            alphas_warped = warp_alpha_axis(alphas, threshold_alpha, power=warp_power)
            threshold_warped = warp_alpha_axis(threshold_alpha, threshold_alpha, power=warp_power)
        else:
            alphas_warped = alphas
            threshold_warped = None
        
        # Plot confidence interval (shaded region)
        if runs > 1:
            ax.fill_between(
                alphas_warped,
                dists_mean - dists_std,
                dists_mean + dists_std,
                alpha=0.3,
                color='teal',
                label='±1 std'
            )
        
        # Plot mean distance vs alpha with error bars
        if runs > 1:
            ax.errorbar(
                alphas_warped,
                dists_mean,
                yerr=dists_std,
                fmt='o-',
                color='teal',
                linewidth=2,
                markersize=6,
                capsize=4,
                capthick=1.5,
                label='Mean distance'
            )
        else:
            # Single run: just plot the line
            ax.plot(alphas_warped, dists_mean, 'o-', color='teal', linewidth=2, label='Distance')
        
        # Compute and plot dynamic threshold
        if threshold_warped is not None:
            ax.axvline(x=threshold_warped, color='gray', linestyle='--', alpha=0.5, 
                       label=f'Threshold α≈{threshold_alpha:.3f}')
        
        # Set title and labels
        if title is None:
            title = "Phase Transition: Anchoring vs. Fairness"
        ax.set_title(title, fontsize=self.PLOT_TITLE_FONTSIZE, fontweight='bold')
        ax.set_xlabel(r"Anchoring Parameter ($\alpha$)", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax.set_ylabel("Distance of Outcome\nfrom Center (Tie)", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=self.PLOT_LEGEND_FONTSIZE)
        ax.tick_params(axis='both', which='major', labelsize=self.PLOT_TICK_LABELSIZE)
        
        # Set custom x-ticks to show original alpha values
        if threshold_alpha is not None:
            # Generate evenly spaced tick positions in original alpha space
            alpha_min, alpha_max = alphas.min(), alphas.max()
            # Use a reasonable number of ticks (5-7)
            n_ticks = 6
            tick_alphas_original = np.linspace(alpha_min, alpha_max, n_ticks)
            # Transform to warped space for tick positions
            tick_positions_warped = warp_alpha_axis(tick_alphas_original, threshold_alpha, power=warp_power)
            # Labels show original alpha values
            ax.set_xticks(tick_positions_warped)
            ax.set_xticklabels([f'{a:.2f}' for a in tick_alphas_original])
        
        plt.tight_layout()
        
        return fig


# Backward compatibility wrapper
def plot_phase_transition(*args, **kwargs):
    """Backward compatibility wrapper for plot_phase_transition function."""
    plotter = PhaseTransitionPlot()
    return plotter.plot(*args, **kwargs)
