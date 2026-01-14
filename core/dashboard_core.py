"""Core simulation logic for dashboard view."""

import numpy as np
from core.utils import spawn_rng
from core.phase_transition import (
    run_phase_transition,
    compute_threshold_alpha,
    find_before_after_alphas,
)
from core.voting_system import run_full_scenario_for_alpha


def run_dashboard_simulation(n=15, m=3, seed=0, baselines=None, eta=0.2, beta=3.0, T=300):
    """
    Run dashboard simulation and return results data.
    
    Args:
        n: Number of voters
        m: Number of candidates
        seed: Random seed for reproducibility
        baselines: Optional list of baseline permutation indices (length n), or None for random sampling
        eta: Learning rate parameter (default: 0.2)
        beta: Sharpness parameter (default: 3.0)
        T: Number of time steps for heatmap/ternary (default: 300)
    
    Returns:
        Dictionary with simulation results containing:
        - alphas: Array of alpha values tested
        - dists: Array of distances from center for each alpha
        - threshold_alpha: Computed threshold alpha value
        - alpha_before: Alpha value before threshold
        - alpha_after: Alpha value after threshold
        - heatmap: Dictionary with strategies, perms, traj, and alpha
        - ternary: Dictionary with traj_before and traj_after (if m=3)
    """
    rng_phase = np.random.default_rng(seed)

    alphas, dists_mean, _ = run_phase_transition(n=n, m=m, seed=seed, rng=rng_phase, baselines=baselines)
    threshold_alpha = compute_threshold_alpha(alphas, dists_mean)
    alpha_before, alpha_after = find_before_after_alphas(alphas, threshold_alpha)
    if alpha_before is None or alpha_after is None:
        alpha_before = 0.05
        alpha_after = 0.60
        
    ternary = {"traj_before": None, "traj_after": None}
    strategies = None
    perms = None
    traj_heatmap = None
    
    if m == 3:
        # Run before/after threshold simulations using run_full_scenario_for_alpha
        # to get both trajectories (for ternary plots) and strategies (for heatmap)
        if alpha_before is not None:
            strategies_before, perms_before, traj_before = run_full_scenario_for_alpha(
                alpha_before, T=T, n=n, m=m, eta=eta, beta=beta, seed=seed, rng=None, baselines=baselines
            )
            ternary["traj_before"] = traj_before
            # Reuse strategies and perms from before run for heatmap
            strategies = strategies_before
            perms = perms_before
            traj_heatmap = traj_before
        
        if alpha_after is not None:
            _, _, traj_after = run_full_scenario_for_alpha(
                alpha_after, T=T, n=n, m=m, eta=eta, beta=beta, seed=seed, rng=None, baselines=baselines
            )
            ternary["traj_after"] = traj_after
    else:
        # Fallback: for non-ternary cases, use alpha_before if available
        if alpha_before is not None:
            strategies, perms, traj_heatmap = run_full_scenario_for_alpha(
                alpha_before, n=n, m=m, eta=eta, beta=beta, T=T, seed=seed, rng=None, baselines=baselines
            )
        ternary = {"traj_before": None, "traj_after": None}
    
    results = {
        "alphas": alphas,
        "dists": dists_mean,
        "threshold_alpha": threshold_alpha,
        "alpha_before": alpha_before,
        "alpha_after": alpha_after,
        "heatmap": {
            "strategies": strategies,
            "perms": perms,
            "traj": traj_heatmap,
            "alpha": alpha_before,
        },
        "ternary": ternary,
    }
    
    return results
