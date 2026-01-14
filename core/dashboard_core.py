"""Core simulation logic for dashboard view."""

import numpy as np
from core.utils import spawn_rng
from core.phase_transition import (
    run_phase_transition,
    compute_threshold_alpha,
    find_before_after_alphas,
)
from core.voting_system import run_full_scenario_for_alpha, IterativeVotingSystem


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
    
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"R","location":"dashboard_core.py:40","message":"After phase transition, before dashboard simulations","data":{{"rng_phase_state":{rng_phase.bit_generator.state if hasattr(rng_phase, "bit_generator") else "unknown"}}}}}\n')
    # #endregion
    threshold_alpha = compute_threshold_alpha(alphas, dists_mean)
    alpha_before, alpha_after = find_before_after_alphas(alphas, threshold_alpha)
    
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"dashboard_core.py:40","message":"After find_before_after_alphas","data":{{"threshold_alpha":{threshold_alpha},"alpha_before":{alpha_before},"alpha_after":{alpha_after},"alpha_before_equals_threshold":{alpha_before == threshold_alpha if alpha_before is not None and threshold_alpha is not None else None}}}}}\n')
    # #endregion
    
    if alpha_before is None or alpha_after is None:
        alpha_before = 0.05
        alpha_after = 0.60
        
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"J","location":"dashboard_core.py:44","message":"Final alpha values","data":{{"threshold_alpha":{threshold_alpha},"alpha_before":{alpha_before},"alpha_after":{alpha_after},"alpha_before_equals_threshold":{alpha_before == threshold_alpha if alpha_before is not None and threshold_alpha is not None else None}}}}}\n')
    # #endregion
        
    ternary = {"traj_before": None, "traj_after": None}
    strategies = None
    perms = None
    traj_heatmap = None
    
    if m == 3:
        # Run before/after threshold simulations using run_full_scenario_for_alpha
        # to get both trajectories (for ternary plots) and strategies (for heatmap)
        # Use burn_in=200 to match phase transition simulation method for consistency
        burn_in = 200
        if alpha_before is not None:
            # Use same simulation method as phase transition: burn_in first, then trajectory
            # Phase transition uses run_seed = seed + run_idx where run_idx=0 for first run
            # So we use seed + 0 = seed to match
            run_idx = 0  # First (and only) run, matching phase transition
            run_seed = (seed + run_idx) if seed is not None else None
            rng_before = np.random.default_rng(run_seed)
            # #region agent log
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"V","location":"dashboard_core.py:73","message":"Dashboard RNG initialization for alpha_before","data":{{"alpha_before":{alpha_before},"seed":{seed},"run_idx":{run_idx},"run_seed":{run_seed},"baselines_provided":{baselines is not None}}}}}\n')
            # #endregion
            sys_before = IterativeVotingSystem(m=m, n=n, alpha=alpha_before, eta=eta, beta=beta, rng=rng_before, baselines=baselines, use_expected_score=False)
            # #region agent log
            x_initial = sys_before.x.copy()
            x_initial_hash = hash(tuple(x_initial.flatten()))
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                sys_baselines_list = list(sys_before.baselines) if hasattr(sys_before.baselines, '__iter__') else sys_before.baselines
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"X","location":"dashboard_core.py:78","message":"Dashboard system initialized for alpha_before","data":{{"alpha_before":{alpha_before},"x_initial_hash":{x_initial_hash},"x_initial_sum":{float(np.sum(x_initial))},"sys_baselines":{sys_baselines_list}}}}}\n')
            # #endregion
            # Burn-in phase (matching phase transition)
            # Log first few steps to compare with phase transition
            p_after_step_1 = None
            p_after_step_2 = None
            for step_idx in range(burn_in):
                p = sys_before.step()
                if step_idx == 0:
                    p_after_step_1 = p.copy()
                elif step_idx == 1:
                    p_after_step_2 = p.copy()
            # #region agent log
            p_after_burnin = sys_before.step()  # Get state after burn-in
            x_after_burnin = sys_before.x.copy()
            x_after_burnin_hash = hash(tuple(x_after_burnin.flatten()))
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"Y","location":"dashboard_core.py:95","message":"Dashboard burn-in steps","data":{{"alpha_before":{alpha_before},"p_after_step_1":{list(p_after_step_1) if p_after_step_1 is not None else None},"p_after_step_2":{list(p_after_step_2) if p_after_step_2 is not None else None},"x_after_burnin_hash":{x_after_burnin_hash}}}}}\n')
            # #endregion
            center = np.array([1 / m] * m)
            dist_after_burnin = np.linalg.norm(p_after_burnin - center)
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"P","location":"dashboard_core.py:72","message":"After burn_in at alpha_before","data":{{"alpha_before":{alpha_before},"burn_in":{burn_in},"p_after_burnin":{list(p_after_burnin)},"dist_after_burnin":{dist_after_burnin}}}}}\n')
            # #endregion
            # Then collect trajectory (start from the step we already took)
            traj_before = [p_after_burnin]
            for step_idx in range(T - 1):
                p = sys_before.step()
                traj_before.append(p)
                # #region agent log
                if step_idx < 5 or step_idx == 50 or step_idx == 100 or step_idx == 200 or step_idx == T - 2:
                    dist_step = np.linalg.norm(p - center)
                    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"S","location":"dashboard_core.py:91","message":"Trajectory step at alpha_before","data":{{"alpha_before":{alpha_before},"step_idx":{step_idx},"p":{list(p)},"dist":{dist_step}}}}}\n')
                # #endregion
            traj_before = np.array(traj_before)
            # strategy_history includes burn-in steps, but trajectory only includes post-burn-in steps
            # Take only the last T entries from strategy_history to match trajectory length
            strategy_history_array = np.array(sys_before.strategy_history)
            if len(strategy_history_array) >= T:
                strategies_before = strategy_history_array[-T:].T  # Shape [n, T]
            else:
                # Fallback: use all if somehow we have fewer than T entries
                strategies_before = strategy_history_array.T
            perms_before = sys_before.perms
            # #region agent log
            center = np.array([1 / m] * m)
            # Compute average of last 50 steps (similar to phase transition collection_steps)
            avg_p_dashboard = np.mean(traj_before[-50:], axis=0) if len(traj_before) >= 50 else np.mean(traj_before, axis=0)
            dist_dashboard = np.linalg.norm(avg_p_dashboard - center)
            # Compute distances for all trajectory steps
            all_dists = [np.linalg.norm(p - center) for p in traj_before]
            dist_first_50_avg = np.mean(all_dists[:50]) if len(all_dists) >= 50 else np.mean(all_dists)
            # Also compute final step
            final_p = traj_before[-1] if len(traj_before) > 0 else None
            dist_final = np.linalg.norm(final_p - center) if final_p is not None else None
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"N","location":"dashboard_core.py:113","message":"Dashboard simulation at alpha_before (with burn_in)","data":{{"alpha_before":{alpha_before},"burn_in":{burn_in},"T":{T},"avg_p_dashboard":{list(avg_p_dashboard)},"dist_dashboard":{dist_dashboard},"final_p":{list(final_p) if final_p is not None else None},"dist_final":{dist_final},"dist_first_50_avg":{dist_first_50_avg},"dist_last_50_avg":{np.mean(all_dists[-50:]) if len(all_dists) >= 50 else None}}}}}\n')
            # #endregion
            ternary["traj_before"] = traj_before
            # Reuse strategies and perms from before run for heatmap
            strategies = strategies_before
            perms = perms_before
            traj_heatmap = traj_before
        
        if alpha_after is not None:
            # Use same simulation method as phase transition: burn_in first, then trajectory
            # Phase transition uses run_seed = seed + run_idx where run_idx=0 for first run
            run_idx = 0  # First (and only) run, matching phase transition
            run_seed = (seed + run_idx) if seed is not None else None
            rng_after = np.random.default_rng(run_seed)
            sys_after = IterativeVotingSystem(m=m, n=n, alpha=alpha_after, eta=eta, beta=beta, rng=rng_after, baselines=baselines, use_expected_score=False)
            # Burn-in phase (matching phase transition)
            for _ in range(burn_in):
                sys_after.step()
            # #region agent log
            p_after_burnin = sys_after.step()  # Get state after burn-in
            center = np.array([1 / m] * m)
            dist_after_burnin = np.linalg.norm(p_after_burnin - center)
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"Q","location":"dashboard_core.py:100","message":"After burn_in at alpha_after","data":{{"alpha_after":{alpha_after},"burn_in":{burn_in},"p_after_burnin":{list(p_after_burnin)},"dist_after_burnin":{dist_after_burnin}}}}}\n')
            # #endregion
            # Then collect trajectory (start from the step we already took)
            traj_after = [p_after_burnin]
            for _ in range(T - 1):
                p = sys_after.step()
                traj_after.append(p)
            traj_after = np.array(traj_after)
            # #region agent log
            center = np.array([1 / m] * m)
            # Compute average of last 50 steps (similar to phase transition collection_steps)
            avg_p_dashboard = np.mean(traj_after[-50:], axis=0) if len(traj_after) >= 50 else np.mean(traj_after, axis=0)
            dist_dashboard = np.linalg.norm(avg_p_dashboard - center)
            # Also compute final step
            final_p = traj_after[-1] if len(traj_after) > 0 else None
            dist_final = np.linalg.norm(final_p - center) if final_p is not None else None
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"O","location":"dashboard_core.py:95","message":"Dashboard simulation at alpha_after (with burn_in)","data":{{"alpha_after":{alpha_after},"burn_in":{burn_in},"T":{T},"avg_p_dashboard":{list(avg_p_dashboard)},"dist_dashboard":{dist_dashboard},"final_p":{list(final_p) if final_p is not None else None},"dist_final":{dist_final}}}}}\n')
            # #endregion
            ternary["traj_after"] = traj_after
    else:
        # Fallback: for non-ternary cases, use alpha_before if available
        if alpha_before is not None:
            strategies, perms, traj_heatmap = run_full_scenario_for_alpha(
                alpha_before, n=n, m=m, eta=eta, beta=beta, T=T, seed=seed, rng=None, baselines=baselines, use_expected_score=False
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
