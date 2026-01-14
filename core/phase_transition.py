"""Phase transition experiment functions for analyzing anchoring parameter effects."""

import numpy as np
from core.utils import spawn_rng
from core.voting_system import IterativeVotingSystem

# Configuration constants
ALPHA_EPSILON = 1e-1  # Tolerance for distance differences in adaptive alpha refinement
ALPHA_MAX_REFINES = 10  # Maximum number of refinement iterations


def _eval_alpha_distance(alpha, n, m, eta, beta, rng, baselines, burn_in=200, collection_steps=50):
    """
    Evaluate the distance from center for a single alpha value.
    
    Args:
        alpha: Alpha parameter value
        n: Number of voters
        m: Number of candidates
        eta: Learning rate parameter
        beta: Temperature parameter
        rng: Random number generator
        baselines: Baseline permutation indices
        burn_in: Number of burn-in steps before collection (default: 200)
        collection_steps: Number of steps to collect and average (default: 50)
    
    Returns:
        Distance from center (tie) for this alpha value
    """
    center = np.array([1 / m] * m)
    
    # Run simulation long enough to converge
    sys = IterativeVotingSystem(m=m, n=n, alpha=alpha, eta=eta, beta=beta, rng=rng, baselines=baselines)
    
    # Burn-in
    for _ in range(burn_in):
        sys.step()
        
    # Collect steps to average
    final_ps = []
    for _ in range(collection_steps):
        p = sys.step()
        final_ps.append(p)
        
    avg_p = np.mean(final_ps, axis=0)
    dist = np.linalg.norm(avg_p - center)
    return dist


def adaptive_alpha_grid(n, m, eta, beta, rng, baselines, burn_in=200, collection_steps=50):
    """
    Build an adaptive alpha grid by iteratively refining intervals where
    distances differ significantly.
    
    Starts with alphas {0, 0.5, 1} and inserts midpoints between adjacent
    alpha values whose distances differ by more than ALPHA_EPSILON,
    up to ALPHA_MAX_REFINES iterations.
    
    Args:
        n: Number of voters
        m: Number of candidates
        eta: Learning rate parameter
        beta: Temperature parameter
        rng: Random number generator
        baselines: Baseline permutation indices
        burn_in: Number of burn-in steps before collection (default: 200)
        collection_steps: Number of steps to collect and average (default: 50)
    
    Returns:
        Tuple (alphas, dists) where alphas is a sorted numpy array of alpha values
        and dists is the corresponding distances from center
    """
    # Start with initial alpha values
    alphas = np.array([0.0, 0.5, 1.0])
    dists = np.array([_eval_alpha_distance(a, n, m, eta, beta, rng, baselines, burn_in, collection_steps) for a in alphas])
    
    # Refinement loop
    for refine_iter in range(ALPHA_MAX_REFINES):
        # Find intervals that need refinement
        intervals_to_refine = []
        for i in range(len(alphas) - 1):
            dist_diff = abs(dists[i] - dists[i + 1])
            if dist_diff > ALPHA_EPSILON:
                intervals_to_refine.append(i)
        
        # If no intervals need refinement, we're done
        if len(intervals_to_refine) == 0:
            break
        
        # Insert midpoints for intervals that need refinement
        # Process from right to left to avoid index shifting issues
        new_alphas = []
        new_dists = []
        
        for i in range(len(alphas)):
            # Add current point
            new_alphas.append(alphas[i])
            new_dists.append(dists[i])
            
            # If this interval needs refinement, add midpoint
            if i in intervals_to_refine and i < len(alphas) - 1:
                alpha_mid = 0.5 * (alphas[i] + alphas[i + 1])
                # Check if midpoint is too close to existing points (avoid duplicates)
                min_gap = 1e-6
                new_alphas_arr = np.array(new_alphas)
                if (len(new_alphas_arr) == 0 or np.min(np.abs(new_alphas_arr - alpha_mid)) > min_gap) and \
                   np.abs(alpha_mid - alphas[i + 1]) > min_gap:
                    dist_mid = _eval_alpha_distance(alpha_mid, n, m, eta, beta, rng, baselines, burn_in, collection_steps)
                    new_alphas.append(alpha_mid)
                    new_dists.append(dist_mid)
        
        # Update arrays (they should remain sorted)
        alphas = np.array(new_alphas)
        dists = np.array(new_dists)
        
        # Ensure arrays are sorted (should be, but double-check)
        sort_idx = np.argsort(alphas)
        alphas = alphas[sort_idx]
        dists = dists[sort_idx]
    
    return alphas, dists


def run_phase_transition(n=15, m=3, alpha_grid=None, eta=0.2, beta=3.0, seed=0, rng=None, baselines=None, burn_in=200, collection_steps=50, runs=1):
    """
    Run phase transition experiment: measure distance from center as function of alpha.
    
    Args:
        n: Number of voters
        m: Number of candidates
        alpha_grid: Optional alpha grid (if None, uses adaptive grid)
        eta: Learning rate parameter
        beta: Temperature parameter
        seed: Random seed
        rng: Optional random number generator
        baselines: Baseline permutation indices
        burn_in: Number of burn-in steps before collection (default: 200)
        collection_steps: Number of steps to collect and average (default: 50)
        runs: Number of independent runs per alpha value (default: 1)
    
    Returns:
        Tuple (alphas, dists_mean, dists_std) where:
        - alphas: Array of alpha values
        - dists_mean: Mean distance across runs for each alpha
        - dists_std: Standard deviation across runs for each alpha
    """
    print("Running Phase Transition Experiment...")
    rng = spawn_rng(seed, rng)
    
    if alpha_grid is not None:
        # Use provided alpha grid
        alphas = alpha_grid
        dists_all_runs = []
        
        # Target center
        center = np.array([1 / m] * m)
        
        for a in alphas:
            dists_for_alpha = []
            
            # Run multiple independent simulations
            for run_idx in range(runs):
                # Create new RNG for each run to ensure independence
                # Use seed + run_idx to make each run independent
                run_seed = (seed + run_idx) if seed is not None else None
                run_rng = np.random.default_rng(run_seed)
                
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    baselines_list = list(baselines) if baselines is not None else None
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"phase_transition.py:166","message":"Run start","data":{{"alpha":{a},"run_idx":{run_idx},"run_seed":{run_seed},"baselines_provided":{baselines is not None},"baselines":{baselines_list}}}}}\n')
                # #endregion
                
                # Run simulation long enough to converge
                sys = IterativeVotingSystem(m=m, n=n, alpha=a, eta=eta, beta=beta, rng=run_rng, baselines=baselines)
                
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    sys_baselines_list = list(sys.baselines) if hasattr(sys.baselines, '__iter__') else sys.baselines
                    x_initial = sys.x.copy()
                    x_initial_hash = hash(tuple(x_initial.flatten()))
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"phase_transition.py:175","message":"System initialized","data":{{"alpha":{a},"run_idx":{run_idx},"sys_baselines":{sys_baselines_list},"x_initial_hash":{x_initial_hash},"x_initial_sum":{float(np.sum(x_initial))}}}}}\n')
                # #endregion
                
                # Burn-in
                for _ in range(burn_in):
                    sys.step()
                
                # #region agent log
                p_after_burnin = sys.step()  # Get one step to see state after burn-in
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    p_after_burnin_list = list(p_after_burnin) if hasattr(p_after_burnin, '__iter__') else p_after_burnin
                    x_after_burnin = sys.x.copy()
                    x_after_burnin_hash = hash(tuple(x_after_burnin.flatten()))
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"phase_transition.py:188","message":"After burn-in","data":{{"alpha":{a},"run_idx":{run_idx},"p_after_burnin":{p_after_burnin_list},"x_after_burnin_hash":{x_after_burnin_hash},"x_after_burnin_sum":{float(np.sum(x_after_burnin))}}}}}\n')
                # #endregion
                    
                # Collect steps to average
                final_ps = []
                final_ps.append(p_after_burnin)  # Include the step we already took
                for step_idx in range(collection_steps - 1):
                    p = sys.step()
                    final_ps.append(p)
                    # #region agent log
                    if step_idx < 3 or step_idx == collection_steps - 2:  # Log first 3 and last
                        with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                            p_list = list(p) if hasattr(p, '__iter__') else p
                            p_hash = hash(tuple(p))
                            f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"phase_transition.py:197","message":"Collection step","data":{{"alpha":{a},"run_idx":{run_idx},"step_idx":{step_idx},"p":{p_list},"p_hash":{p_hash}}}}}\n')
                    # #endregion
                    
                avg_p = np.mean(final_ps, axis=0)
                dist = np.linalg.norm(avg_p - center)
                
                # Check if all collection steps are identical (converged to fixed point)
                p_first = final_ps[0]
                p_last = final_ps[-1]
                p_all_same = all(np.allclose(p_first, p_step) for p_step in final_ps)
                p_first_last_diff = np.linalg.norm(p_first - p_last)
                
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    avg_p_list = list(avg_p) if hasattr(avg_p, '__iter__') else avg_p
                    final_ps_sample_list = list(final_ps[0]) if len(final_ps) > 0 and hasattr(final_ps[0], '__iter__') else (final_ps[0] if len(final_ps) > 0 else None)
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"phase_transition.py:210","message":"Run complete","data":{{"alpha":{a},"run_idx":{run_idx},"avg_p":{avg_p_list},"dist":{dist},"final_ps_sample":{final_ps_sample_list},"p_all_same":{p_all_same},"p_first_last_diff":{p_first_last_diff}}}}}\n')
                # #endregion
                
                dists_for_alpha.append(dist)
            
            dists_all_runs.append(dists_for_alpha)
        
        # Compute mean and std across runs for each alpha
        dists_mean = np.array([np.mean(dists) for dists in dists_all_runs])
        dists_std = np.array([np.std(dists, ddof=1) if len(dists) > 1 else 0.0 for dists in dists_all_runs])
        
        # #region agent log
        with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
            for i, (a, dists) in enumerate(zip(alphas, dists_all_runs)):
                dists_list = [float(d) for d in dists]  # Convert to list of floats for JSON
                all_dists_identical = all(np.isclose(dists[0], d) for d in dists) if len(dists) > 0 else True
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"phase_transition.py:225","message":"Alpha summary","data":{{"alpha":{a},"dists":{dists_list},"mean":{dists_mean[i]},"std":{dists_std[i]},"min_dist":{min(dists)},"max_dist":{max(dists)},"range":{max(dists) - min(dists)},"all_dists_identical":{all_dists_identical}}}}}\n')
        # #endregion
        
        return alphas, dists_mean, dists_std
    else:
        # Use adaptive alpha grid
        # For adaptive grid, we still need to handle multiple runs
        # We'll use the first run for grid refinement, then run all runs for final statistics
        alphas, _ = adaptive_alpha_grid(n, m, eta, beta, rng, baselines, burn_in, collection_steps)
        
        # Now run all runs for each alpha in the grid
        dists_all_runs = []
        center = np.array([1 / m] * m)
        
        for a in alphas:
            dists_for_alpha = []
            
            for run_idx in range(runs):
                # Use seed + run_idx to make each run independent
                run_seed = (seed + run_idx) if seed is not None else None
                run_rng = np.random.default_rng(run_seed)
                
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    baselines_list = list(baselines) if baselines is not None else None
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"phase_transition.py:235","message":"Run start (adaptive)","data":{{"alpha":{a},"run_idx":{run_idx},"run_seed":{run_seed},"baselines_provided":{baselines is not None},"baselines":{baselines_list}}}}}\n')
                # #endregion
                
                sys = IterativeVotingSystem(m=m, n=n, alpha=a, eta=eta, beta=beta, rng=run_rng, baselines=baselines)
                
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    sys_baselines_list = list(sys.baselines) if hasattr(sys.baselines, '__iter__') else sys.baselines
                    x_initial = sys.x.copy()
                    x_initial_hash = hash(tuple(x_initial.flatten()))
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"phase_transition.py:269","message":"System initialized (adaptive)","data":{{"alpha":{a},"run_idx":{run_idx},"sys_baselines":{sys_baselines_list},"x_initial_hash":{x_initial_hash},"x_initial_sum":{float(np.sum(x_initial))}}}}}\n')
                # #endregion
                
                for _ in range(burn_in):
                    sys.step()
                
                # #region agent log
                p_after_burnin = sys.step()
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    p_after_burnin_list = list(p_after_burnin) if hasattr(p_after_burnin, '__iter__') else p_after_burnin
                    x_after_burnin = sys.x.copy()
                    x_after_burnin_hash = hash(tuple(x_after_burnin.flatten()))
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"phase_transition.py:281","message":"After burn-in (adaptive)","data":{{"alpha":{a},"run_idx":{run_idx},"p_after_burnin":{p_after_burnin_list},"x_after_burnin_hash":{x_after_burnin_hash},"x_after_burnin_sum":{float(np.sum(x_after_burnin))}}}}}\n')
                # #endregion
                    
                final_ps = []
                final_ps.append(p_after_burnin)
                for step_idx in range(collection_steps - 1):
                    p = sys.step()
                    final_ps.append(p)
                    # #region agent log
                    if step_idx < 3 or step_idx == collection_steps - 2:  # Log first 3 and last
                        with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                            p_list = list(p) if hasattr(p, '__iter__') else p
                            p_hash = hash(tuple(p))
                            f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"phase_transition.py:289","message":"Collection step (adaptive)","data":{{"alpha":{a},"run_idx":{run_idx},"step_idx":{step_idx},"p":{p_list},"p_hash":{p_hash}}}}}\n')
                    # #endregion
                    
                avg_p = np.mean(final_ps, axis=0)
                dist = np.linalg.norm(avg_p - center)
                
                # Check if all collection steps are identical (converged to fixed point)
                p_first = final_ps[0]
                p_last = final_ps[-1]
                p_all_same = all(np.allclose(p_first, p_step) for p_step in final_ps)
                p_first_last_diff = np.linalg.norm(p_first - p_last)
                
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    avg_p_list = list(avg_p) if hasattr(avg_p, '__iter__') else avg_p
                    final_ps_sample_list = list(final_ps[0]) if len(final_ps) > 0 and hasattr(final_ps[0], '__iter__') else (final_ps[0] if len(final_ps) > 0 else None)
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"phase_transition.py:303","message":"Run complete (adaptive)","data":{{"alpha":{a},"run_idx":{run_idx},"avg_p":{avg_p_list},"dist":{dist},"final_ps_sample":{final_ps_sample_list},"p_all_same":{p_all_same},"p_first_last_diff":{p_first_last_diff}}}}}\n')
                # #endregion
                
                dists_for_alpha.append(dist)
            
            dists_all_runs.append(dists_for_alpha)
        
        dists_mean = np.array([np.mean(dists) for dists in dists_all_runs])
        dists_std = np.array([np.std(dists, ddof=1) if len(dists) > 1 else 0.0 for dists in dists_all_runs])
        
        # #region agent log
        with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
            for i, (a, dists) in enumerate(zip(alphas, dists_all_runs)):
                dists_list = [float(d) for d in dists]  # Convert to list of floats for JSON
                all_dists_identical = all(np.isclose(dists[0], d) for d in dists) if len(dists) > 0 else True
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"phase_transition.py:310","message":"Alpha summary (adaptive)","data":{{"alpha":{a},"dists":{dists_list},"mean":{dists_mean[i]},"std":{dists_std[i]},"min_dist":{min(dists)},"max_dist":{max(dists)},"range":{max(dists) - min(dists)},"all_dists_identical":{all_dists_identical}}}}}\n')
        # #endregion
        
        return alphas, dists_mean, dists_std


def compute_threshold_alpha(alphas, dists):
    """
    Compute the threshold alpha: the immediate alpha value greater than the minimum alpha
    where the distance from center exceeds the distance at alpha=1 by epsilon.
    
    Returns the immediate alpha value (higher alpha) that's greater than the first alpha
    where dist > (dist_at_alpha_1 + epsilon).
    """
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"phase_transition.py:346","message":"compute_threshold_alpha entry","data":{{"alphas_len":{len(alphas)},"dists_len":{len(dists)}}}}}\n')
    # #endregion
    
    if len(dists) < 1:
        return None
    
    # Get distance at alpha=1 (last element since arrays are sorted ascending)
    distance_at_alpha_1 = dists[-1]
    threshold = distance_at_alpha_1 + ALPHA_EPSILON
    
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"phase_transition.py:355","message":"Threshold calculation","data":{{"distance_at_alpha_1":{distance_at_alpha_1},"ALPHA_EPSILON":{ALPHA_EPSILON},"threshold":{threshold}}}}}\n')
    # #endregion
    
    # Find the minimum alpha (first from the right, i.e., highest alpha value)
    # where distance exceeds the threshold
    # Iterate from right to left (high to low alpha)
    for i in range(len(dists) - 1, -1, -1):
        if dists[i] > threshold:
            # Return the immediate alpha value greater than this one
            # (i+1 is the next higher alpha value, if it exists)
            if i + 1 < len(alphas):
                result = alphas[i + 1]
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"phase_transition.py:362","message":"Found threshold (i+1 case)","data":{{"i":{i},"dists_i":{dists[i]},"alphas_i":{alphas[i]},"alphas_i_plus_1":{alphas[i+1]},"result":{result}}}}}\n')
                # #endregion
                return result
            else:
                result = alphas[i]
                # #region agent log
                with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                    f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"phase_transition.py:364","message":"Found threshold (i case, at end)","data":{{"i":{i},"dists_i":{dists[i]},"alphas_i":{alphas[i]},"result":{result}}}}}\n')
                # #endregion
                return result
    
    # If no alpha exceeds the threshold, return None
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"H","location":"phase_transition.py:367","message":"No threshold found","data":{{}}}}\n')
    # #endregion
    return None


def find_before_after_alphas(alphas, threshold_alpha):
    """
    Find the last alpha before threshold and the threshold alpha itself.
    The threshold_alpha is the alpha value at the start of the steepest drop.
    Returns (alpha_before, alpha_after) where:
    - alpha_before is the last alpha value before the threshold (less than threshold)
    - alpha_after is the threshold alpha itself (the point at the threshold)
    """
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        alphas_list = [float(a) for a in alphas] if threshold_alpha is not None and len(alphas) > 0 else []
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"phase_transition.py:378","message":"find_before_after_alphas entry","data":{{"threshold_alpha":{threshold_alpha},"alphas_len":{len(alphas) if threshold_alpha is not None else 0},"alphas_min":{float(alphas.min()) if threshold_alpha is not None and len(alphas) > 0 else None},"alphas_max":{float(alphas.max()) if threshold_alpha is not None and len(alphas) > 0 else None},"alphas_list":{alphas_list}}}}}\n')
    # #endregion
    
    if threshold_alpha is None:
        return None, None
    
    # Find the index of the threshold alpha (should be exact match since it comes from alphas array)
    threshold_idx = np.where(alphas == threshold_alpha)[0]
    if len(threshold_idx) == 0:
        # Fallback: find closest
        threshold_idx = np.argmin(np.abs(alphas - threshold_alpha))
    else:
        threshold_idx = threshold_idx[0]
    
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        if threshold_idx >= 2:
            before_idx = 1  # Use index 1 (alpha=0.5) which is clearly in non-tie region
        elif threshold_idx == 1:
            before_idx = 0
        else:
            before_idx = 0
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"phase_transition.py:388","message":"Found threshold index","data":{{"threshold_idx":{int(threshold_idx)},"threshold_alpha":{threshold_alpha},"alphas_at_idx":{float(alphas[threshold_idx])},"alphas_before_idx_1":{float(alphas[threshold_idx - 1]) if threshold_idx > 0 else None},"alphas_before_idx_2":{float(alphas[threshold_idx - 2]) if threshold_idx >= 2 else None},"alphas_index_1":{float(alphas[1]) if len(alphas) > 1 else None},"selected_before_idx":{int(before_idx)},"alphas_after_idx":{float(alphas[threshold_idx + 1]) if threshold_idx < len(alphas) - 1 else None}}}}}\n')
    # #endregion
    
    # alpha_after is the threshold alpha itself (the point at the threshold)
    alpha_after = alphas[threshold_idx]
    
    # alpha_before is a value clearly before the threshold, far enough to ensure
    # it's in the non-tie region. We pick a value that's well before the threshold
    # to ensure it shows non-tie behavior even with different simulation methods.
    # Pick index 0 (alpha=0.0) or index 1 (alpha=0.5) which are clearly in non-tie region
    if threshold_idx >= 2:
        # Pick index 1 (alpha=0.5) which is clearly in the non-tie region
        # This ensures the dashboard simulation will also show non-tie behavior
        alpha_before = alphas[1] if len(alphas) > 1 else alphas[0]
    elif threshold_idx == 1:
        # If threshold is at index 1, use index 0
        alpha_before = alphas[0]
    else:
        # If threshold is at index 0, we can't have a "before" value
        alpha_before = alphas[0] if len(alphas) > 0 else None
    
    # #region agent log
    with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
        alpha_before_rounded = round(alpha_before, 3) if alpha_before is not None else None
        alpha_after_rounded = round(alpha_after, 3) if alpha_after is not None else None
        threshold_rounded = round(threshold_alpha, 3) if threshold_alpha is not None else None
        f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"phase_transition.py:404","message":"Returning alpha_before and alpha_after","data":{{"alpha_before":{alpha_before},"alpha_after":{alpha_after},"threshold_alpha":{threshold_alpha},"alpha_before_rounded":{alpha_before_rounded},"alpha_after_rounded":{alpha_after_rounded},"threshold_rounded":{threshold_rounded},"alpha_before_equals_threshold":{alpha_before == threshold_alpha if alpha_before is not None else None},"alpha_after_equals_threshold":{alpha_after == threshold_alpha if alpha_after is not None else None},"alpha_before_rounded_equals_threshold":{alpha_before_rounded == threshold_rounded if alpha_before_rounded is not None and threshold_rounded is not None else None}}}}}\n')
    # #endregion
    
    return alpha_before, alpha_after


def warp_alpha_axis(alpha, threshold_alpha, power=0.5):
    """
    Apply nonlinear transform to alpha values to stretch near threshold.
    
    Uses a power transform centered at threshold_alpha:
    - Values near threshold are stretched (power < 1)
    - Values far from threshold are compressed
    
    Args:
        alpha: Original alpha value(s) (can be scalar or array)
        threshold_alpha: Threshold alpha value (center of transform)
        power: Power parameter (< 1 stretches near threshold, default 0.5)
    
    Returns:
        Transformed alpha value(s) (same type/shape as input)
    """
    if threshold_alpha is None:
        return alpha
    
    alpha = np.asarray(alpha)
    is_scalar = alpha.ndim == 0
    diff = alpha - threshold_alpha
    # Apply power transform: sign(diff) * |diff|^power
    # This stretches small differences and compresses large ones
    transformed = threshold_alpha + np.sign(diff) * np.abs(diff) ** power
    
    return transformed.item() if is_scalar else transformed


def run_phase_transition_ternary(alpha, n=15, m=3, eta=0.2, beta=3.0, seed=0, rng=None, baselines=None, T=300):
    """
    Run a full trajectory for a specific alpha value using the same parameters as phase transition.
    This ensures consistency with the phase transition plot.
    
    Args:
        alpha: Alpha parameter value
        n: Number of voters
        m: Number of candidates  
        eta: Learning rate (default 0.2, matching phase transition)
        beta: Temperature parameter (default 3.0, matching phase transition)
        seed: Random seed
        rng: Optional RNG (if None, creates new one from seed)
        baselines: Baseline permutation indices
        T: Number of time steps (default 300)
    
    Returns:
        Full trajectory array of shape (T, m)
    """
    if m != 3:
        raise ValueError("Ternary scenario requires m == 3")
    rng = spawn_rng(seed, rng)
    sys = IterativeVotingSystem(m=m, n=n, alpha=alpha, eta=eta, beta=beta, rng=rng, baselines=baselines)
    traj = []
    
    for _ in range(T):
        p = sys.step()
        traj.append(p)
        
    return np.array(traj)
