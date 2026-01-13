"""Dashboard plotting function for combined 2×3 grid view."""

import numpy as np
import matplotlib.pyplot as plt
from core.rankings_core import candidate_labels
from core.phase_transition import warp_alpha_axis
from plots.plot_voter_strategies import plot_voter_strategies
from plots.plot_ternary import _project_ternary


def plot_dashboard(data, n=15, m=3, seed=0):
    """
    Create combined dashboard with 2×3 grid layout.
    
    The dashboard includes:
    - Phase transition plot (top left)
    - Strategy heatmap (top right, spans 2 columns)
    - Ternary plots before/after threshold (bottom left/right)
    - Text explanation panel (bottom right)
    
    Args:
        data: Dictionary with simulation results containing:
            - alphas: Array of alpha values tested
            - dists: Array of distances from center for each alpha
            - threshold_alpha: Computed threshold alpha value
            - alpha_before: Alpha value before threshold
            - alpha_after: Alpha value after threshold
            - heatmap: Dictionary with strategies, perms, traj, and alpha
            - ternary: Dictionary with traj_before and traj_after (if m=3)
        n: Number of voters (for labels, default: 15)
        m: Number of candidates (for labels, default: 3)
        seed: Random seed (for labels, default: 0)
    
    Returns:
        matplotlib.figure.Figure: The figure object containing the dashboard
    """
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3)
    
    alphas = data["alphas"]
    dists = data["dists"]
    threshold_alpha = data["threshold_alpha"]
    alpha_before = data["alpha_before"]
    alpha_after = data["alpha_after"]
    strategies = data["heatmap"]["strategies"]
    perms = data["heatmap"]["perms"]
    traj = data["heatmap"]["traj"]
    ternary = data.get("ternary")
    labels = candidate_labels(m)
    
    # A. Phase Transition Plot
    ax_phase = fig.add_subplot(gs[0, 0])
    
    # Apply nonlinear transform to stretch x-axis near threshold
    warp_power = 0.4  # Power parameter: lower values = more stretching near threshold
    if threshold_alpha is not None:
        alphas_warped = warp_alpha_axis(alphas, threshold_alpha, power=warp_power)
        threshold_warped = warp_alpha_axis(threshold_alpha, threshold_alpha, power=warp_power)
    else:
        alphas_warped = alphas
        threshold_warped = None
    
    ax_phase.plot(alphas_warped, dists, 'o-', color='teal', linewidth=2)
    
    # Compute and plot dynamic threshold
    if threshold_warped is not None:
        ax_phase.axvline(x=threshold_warped, color='gray', linestyle='--', alpha=0.5, 
                         label=f'Threshold α≈{threshold_alpha:.2f}')
    
    ax_phase.set_title("Phase Transition: Anchoring vs. Fairness")
    ax_phase.set_xlabel(r"Anchoring Parameter ($\alpha$)")
    ax_phase.set_ylabel("Distance of Outcome from Center (Tie)")
    ax_phase.grid(True, alpha=0.3)
    ax_phase.legend()
    
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
        ax_phase.set_xticks(tick_positions_warped)
        ax_phase.set_xticklabels([f'{a:.2f}' for a in tick_alphas_original])
    
    # B. Strategy Heatmap
    ax_heat = fig.add_subplot(gs[0, 1:])
    plot_voter_strategies(
        strategies,
        perms,
        labels=labels,
        ax=ax_heat,
        title=rf"Voter Strategy Evolution ($\alpha={data['heatmap']['alpha']:.3f}$)"
    )
    
    # C. Ternary Trajectories (Before and After Threshold)
    if ternary is not None and ternary.get("traj_before") is not None and ternary.get("traj_after") is not None:
        traj_before = ternary["traj_before"]
        traj_after = ternary["traj_after"]
        T = len(traj_before)
        
        # Plot Before Threshold
        ax_tern_before = fig.add_subplot(gs[1, 0])
        avg_traj_before = np.cumsum(traj_before, axis=0) / np.arange(1, T + 1)[:, None]
        
        tri_x = [0, 1, 0.5, 0]
        tri_y = [0, 0, np.sqrt(3)/2, 0]
        ax_tern_before.plot(tri_x, tri_y, 'k-', lw=1)
        ax_tern_before.text(0.5, np.sqrt(3)/2 + 0.02, f'Cand {labels[0]}', ha='center')
        ax_tern_before.text(1.02, -0.05, f'Cand {labels[1]}', ha='center')
        ax_tern_before.text(-0.02, -0.05, f'Cand {labels[2]}', ha='center')
        
        ix_before, iy_before = _project_ternary(traj_before)
        ax_tern_before.plot(ix_before, iy_before, 'gray', alpha=0.3, lw=0.5, label='Instantaneous $p^t$')
        
        ax_before, ay_before = _project_ternary(avg_traj_before)
        ax_tern_before.plot(ax_before, ay_before, 'b-', lw=2, label='Running Avg')
        ax_tern_before.scatter(ax_before[0], ay_before[0], c='red', marker='x', s=100, label='Start', zorder=10)
        ax_tern_before.scatter(ax_before[-1], ay_before[-1], c='blue', marker='*', s=150, label='End (Avg)', zorder=10)
        
        ax_tern_before.set_title(f"Before Threshold ($\\alpha={alpha_before:.3f}$)")
        ax_tern_before.axis('off')
        ax_tern_before.set_aspect('equal')
        
        # Plot After Threshold
        ax_tern_after = fig.add_subplot(gs[1, 1])
        avg_traj_after = np.cumsum(traj_after, axis=0) / np.arange(1, T + 1)[:, None]
        
        ax_tern_after.plot(tri_x, tri_y, 'k-', lw=1)
        ax_tern_after.text(0.5, np.sqrt(3)/2 + 0.02, f'Cand {labels[0]}', ha='center')
        ax_tern_after.text(1.02, -0.05, f'Cand {labels[1]}', ha='center')
        ax_tern_after.text(-0.02, -0.05, f'Cand {labels[2]}', ha='center')
        
        ix_after, iy_after = _project_ternary(traj_after)
        ax_tern_after.plot(ix_after, iy_after, 'gray', alpha=0.3, lw=0.5, label='Instantaneous $p^t$')
        
        ax_after, ay_after = _project_ternary(avg_traj_after)
        ax_tern_after.plot(ax_after, ay_after, 'b-', lw=2, label='Running Avg')
        ax_tern_after.scatter(ax_after[0], ay_after[0], c='red', marker='x', s=100, label='Start', zorder=10)
        ax_tern_after.scatter(ax_after[-1], ay_after[-1], c='blue', marker='*', s=150, label='End (Avg)', zorder=10)
        
        ax_tern_after.set_title(f"After Threshold ($\\alpha={alpha_after:.3f}$)")
        ax_tern_after.axis('off')
        ax_tern_after.set_aspect('equal')
        # Single legend for both ternary plots (positioned between plots)
        ax_tern_after.legend(
            loc='upper right',
            bbox_to_anchor=(-0.15, 1.0),  # shift legend left into the gap between plots
            fontsize=8,
        )
    else:
        ax_placeholder = fig.add_subplot(gs[1, :2])
        ax_placeholder.axis('off')
        ax_placeholder.text(0.5, 0.5, "Ternary plot requires m=3", ha='center', va='center', fontsize=12)

    # D. Text Explanation
    ax_text = fig.add_subplot(gs[1, 2])
    ax_text.axis('off')
    # Use three decimals here as well so the explanatory text matches the precise values in the ternary titles
    thr_str = f"{threshold_alpha:.3f}" if threshold_alpha is not None else "N/A"
    before_str = f"{alpha_before:.3f}" if alpha_before is not None else "N/A"
    after_str = f"{alpha_after:.3f}" if alpha_after is not None else "N/A"
    heat_alpha = data["heatmap"].get("alpha", None)
    heat_alpha_str = f"{heat_alpha:.3f}" if heat_alpha is not None else "N/A"
    
    # Format text with moderate line breaks - more vertical than original but wider than too-tight version
    text_str = (
        "INTERPRETATION:\n\n"
        "1. Phase Transition (Top Left):\n"
        f"   Steep drop detected near α≈{thr_str}.\n"
        f"   Example slices shown at α≈{before_str} (before)\n"
        f"   and α≈{after_str} (after).\n"
        "   Below the drop, strategies push\n"
        "   outcome away from the tie.\n"
        "   Above the drop, anchoring pulls\n"
        "   outcome back toward fair tie.\n\n"
        "2. Strategy Heatmap (Top Right):\n"
        "   Each row is a voter; colors are\n"
        "   their reported rankings.\n"
        f"   This heatmap uses α={heat_alpha_str}.\n"
        "   Blocks of shared color show\n"
        "   voters coordinating and\n"
        "   switching ranks together."
    )
    ax_text.text(0, 0.5, text_str, va='center', fontsize=12, family='monospace')

    plt.tight_layout()
    return fig
