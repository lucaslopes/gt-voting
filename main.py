import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog
from itertools import permutations
import matplotlib.colors as mcolors
import argparse
from math import factorial
from core.utils import spawn_rng
from core.rankings_core import candidate_labels
from core.honest_reports import parse_baselines

# ==========================================
# Configuration Constants
# ==========================================
ALPHA_EPSILON = 1e-2  # Tolerance for distance differences in adaptive alpha refinement
ALPHA_MAX_REFINES = 10  # Maximum number of refinement iterations

# ==========================================
# 1. Core Model (Optimized)
# ==========================================


class IterativeVotingSystem:
    def __init__(self, m, n, alpha, eta, beta, baselines=None, rng=None):
        self.m = m
        self.n = n
        self.alpha = alpha
        self.eta = eta
        self.beta = beta
        self.rng = spawn_rng(None, rng)
        
        # Complete graph or a "clique" (all voters are connected to all others)
        self.adj = np.ones((n, n)) - np.eye(n)
        
        # Permutations
        self.perms = list(permutations(range(m)))
        self.n_perms = len(self.perms)
        
        # Rank vectors: [n_perms, m]
        self.rank_vectors = np.zeros((self.n_perms, m))
        for i, p in enumerate(self.perms):
            for rank, candidate in enumerate(p):
                self.rank_vectors[i, candidate] = rank
        
        # Baselines sampled uniformly (reproducible via rng/seed)
        if baselines is None:
            self.baselines = self.rng.choice(self.n_perms, size=n)
        else:
            self.baselines = np.asarray(baselines)
            
        # Initialize X at baselines
        self.x = np.zeros((n, self.n_perms))
        for i, base_idx in enumerate(self.baselines):
            self.x[i, base_idx] = 1.0

        # For visualization tracking
        self.strategy_history = [] # Will store most likely rank for each voter
        
    def solve_gt_game(self, M):
        # Solves max_p min_q p^T M q
        c = np.zeros(self.m + 1); c[-1] = -1
        A_ub = np.hstack([-M.T, np.ones((self.m, 1))])
        b_ub = np.zeros(self.m)
        A_eq = np.array([[1.0] * self.m + [0.0]]); b_eq = np.array([1.0])
        bounds = [(0, None)] * self.m + [(None, None)]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
        return res.x[:-1] if res.success else np.ones(self.m)/self.m

    def get_margin_matrix_from_probs(self):
        # Expected Margin Matrix calculation (faster/smoother than sampling)
        # M_ab = Sum_i ( Prob(i ranks a > b) - Prob(i ranks b > a) )
        # This is a deterministic approximation for smoother plots
        M = np.zeros((self.m, self.m))
        
        # Precompute pairwise preference for each permutation
        # pairwise_pref[k, a, b] = 1 if a>b in perm k, -1 if b>a
        if not hasattr(self, 'pairwise_pref'):
            self.pairwise_pref = np.zeros((self.n_perms, self.m, self.m))
            for k, p in enumerate(self.perms):
                for a in range(self.m):
                    for b in range(self.m):
                        if a == b: continue
                        if p.index(a) < p.index(b):
                            self.pairwise_pref[k, a, b] = 1
                        else:
                            self.pairwise_pref[k, a, b] = -1
        
        # Aggregate voter strategies
        # X shape: [n, n_perms]
        # Weighted sum of preferences
        # M[a,b] = sum_i sum_k x[i,k] * pref[k,a,b]
        
        # Sum x across voters -> total weight on each perm
        total_x = np.sum(self.x, axis=0) # [n_perms]
        
        # M[a,b] = sum_k total_x[k] * pairwise_pref[k,a,b]
        for a in range(self.m):
            for b in range(self.m):
                M[a,b] = np.sum(total_x * self.pairwise_pref[:, a, b])
                
        return M

    def step(self):
        # 1. Aggregate (using expected margins for stability in phase plot)
        M = self.get_margin_matrix_from_probs()
        p_t = self.solve_gt_game(M)
        p_tilde = p_t - (1.0 / self.m)
        
        # 2. Update Strategies
        # Score s_i(pi) = - deg_i * <p_tilde, r_pi>
        # (Assuming complete graph, deg_i is const, same logic as before)
        deg = self.n - 1
        scores = -1.0 * deg * (self.rank_vectors @ p_tilde) # Shape [n_perms]
        
        # Logit
        scores -= np.max(scores)
        sbr = np.exp(self.beta * scores)
        sbr /= np.sum(sbr)
        
        # Update x
        # anchor_term: each voter has their own baseline
        for i in range(self.n):
            anchor = np.zeros(self.n_perms)
            anchor[self.baselines[i]] = 1.0
            self.x[i] = (1 - self.eta) * self.x[i] + self.eta * ((1 - self.alpha) * sbr + self.alpha * anchor)
        
        # Record dominant strategy for heatmap
        # Argmax of x[i]
        current_strategies = np.argmax(self.x, axis=1)
        self.strategy_history.append(current_strategies)
            
        return p_t

# ==========================================
# 2. Experiments
# ==========================================

def _eval_alpha_distance(alpha, n, m, eta, beta, rng, baselines):
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
    
    Returns:
        Distance from center (tie) for this alpha value
    """
    center = np.array([1 / m] * m)
    
    # Run simulation long enough to converge
    sys = IterativeVotingSystem(m=m, n=n, alpha=alpha, eta=eta, beta=beta, rng=rng, baselines=baselines)
    
    # Burn-in
    for _ in range(200):
        sys.step()
        
    # Collect last 50 steps to average
    final_ps = []
    for _ in range(50):
        p = sys.step()
        final_ps.append(p)
        
    avg_p = np.mean(final_ps, axis=0)
    dist = np.linalg.norm(avg_p - center)
    return dist


def adaptive_alpha_grid(n, m, eta, beta, rng, baselines):
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
    
    Returns:
        Tuple (alphas, dists) where alphas is a sorted numpy array of alpha values
        and dists is the corresponding distances from center
    """
    # Start with initial alpha values
    alphas = np.array([0.0, 0.5, 1.0])
    dists = np.array([_eval_alpha_distance(a, n, m, eta, beta, rng, baselines) for a in alphas])
    
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
                    dist_mid = _eval_alpha_distance(alpha_mid, n, m, eta, beta, rng, baselines)
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


def run_phase_transition(n=15, m=3, alpha_grid=None, eta=0.2, beta=3.0, seed=0, rng=None, baselines=None):
    print("Running Phase Transition Experiment...")
    rng = spawn_rng(seed, rng)
    
    if alpha_grid is not None:
        # Use provided alpha grid
        alphas = alpha_grid
        dist_from_center = []
        
        # Target center
        center = np.array([1 / m] * m)
        
        for a in alphas:
            # Run simulation long enough to converge
            sys = IterativeVotingSystem(m=m, n=n, alpha=a, eta=eta, beta=beta, rng=rng, baselines=baselines)
            
            # Burn-in
            for _ in range(200):
                sys.step()
                
            # Collect last 50 steps to average
            final_ps = []
            for _ in range(50):
                p = sys.step()
                final_ps.append(p)
                
            avg_p = np.mean(final_ps, axis=0)
            dist = np.linalg.norm(avg_p - center)
            dist_from_center.append(dist)
        
        return alphas, dist_from_center
    else:
        # Use adaptive alpha grid
        alphas, dists = adaptive_alpha_grid(n, m, eta, beta, rng, baselines)
        return alphas, dists

def compute_threshold_alpha(alphas, dists):
    """
    Compute the alpha value at the steepest drop in distance.
    Returns the alpha value where the negative finite difference is maximum.
    """
    if len(dists) < 2:
        return None
    
    # Compute finite differences (negative values indicate drops)
    diffs = np.diff(dists)
    
    # Find the index with the steepest drop (most negative difference)
    steepest_idx = np.argmin(diffs)
    
    # Return the alpha value at the midpoint between the two points
    # where the drop occurs (or the alpha at the start of the drop)
    threshold_alpha = alphas[steepest_idx]
    
    return threshold_alpha

def find_before_after_alphas(alphas, threshold_alpha):
    """
    Find the last alpha before threshold and first alpha after threshold.
    The threshold_alpha is the alpha value at the start of the steepest drop.
    Returns (alpha_before, alpha_after) where:
    - alpha_before is the alpha value at the threshold (last point before drop)
    - alpha_after is the first alpha value after the threshold (first point after drop)
    """
    if threshold_alpha is None:
        return None, None
    
    # Find the index of the threshold alpha (should be exact match since it comes from alphas array)
    threshold_idx = np.where(alphas == threshold_alpha)[0]
    if len(threshold_idx) == 0:
        # Fallback: find closest
        threshold_idx = np.argmin(np.abs(alphas - threshold_alpha))
    else:
        threshold_idx = threshold_idx[0]
    
    # alpha_before is the threshold alpha itself (the last point before the drop)
    alpha_before = alphas[threshold_idx]
    
    # alpha_after is the first alpha after the threshold (the first point after the drop)
    if threshold_idx < len(alphas) - 1:
        alpha_after = alphas[threshold_idx + 1]
    else:
        alpha_after = alphas[-1] if len(alphas) > 0 else None
    
    return alpha_before, alpha_after

def run_ternary_scenario(alpha, T=300, n=15, m=3, eta=0.1, beta=3.0, seed=0, rng=None, baselines=None):
    """
    Run a ternary plot scenario for a given alpha value.
    Returns trajectory array; requires m == 3.
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

def run_heatmap_scenario(n=15, m=3, alpha=0.10, eta=0.1, beta=3.0, T=150, seed=0, rng=None, baselines=None):
    print(f"Running Heatmap Scenario (Alpha={alpha})...")
    rng = spawn_rng(seed, rng)
    sys = IterativeVotingSystem(m=m, n=n, alpha=alpha, eta=eta, beta=beta, rng=rng, baselines=baselines)
    traj = []
    
    for _ in range(T):
        p = sys.step()
        traj.append(p)
        
    return np.array(sys.strategy_history).T, sys.perms, traj # [N, T]


def run_full_scenario_for_alpha(alpha, n=15, m=3, eta=0.2, beta=3.0, T=300, seed=0, rng=None, baselines=None):
    """
    Run a single simulation for a given alpha and return both:
      - strategies: dominant strategy index per voter over time, shape [n, T]
      - perms: permutation list from the underlying system
      - traj: full trajectory of outcome distributions p^t, shape [T, m]
    This helper is used to ensure that the heatmap and ternary plots
    can be driven from the exact same run.
    """
    rng = spawn_rng(seed, rng)
    sys = IterativeVotingSystem(m=m, n=n, alpha=alpha, eta=eta, beta=beta, rng=rng, baselines=baselines)
    traj = []
    
    for _ in range(T):
        p = sys.step()
        traj.append(p)
    
    strategies = np.array(sys.strategy_history).T  # [n, T]
    return strategies, sys.perms, np.array(traj)

# ==========================================
# 3. Plotting
# ==========================================

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


def unwarp_alpha_axis(alpha_warped, threshold_alpha, power=0.5):
    """
    Inverse transform to recover original alpha values from warped space.
    
    Args:
        alpha_warped: Warped alpha value(s) (can be scalar or array)
        threshold_alpha: Threshold alpha value (center of transform)
        power: Power parameter (must match warp_alpha_axis)
    
    Returns:
        Original alpha value(s) (same type/shape as input)
    """
    if threshold_alpha is None:
        return alpha_warped
    
    alpha_warped = np.asarray(alpha_warped)
    is_scalar = alpha_warped.ndim == 0
    diff = alpha_warped - threshold_alpha
    # Inverse power transform: sign(diff) * |diff|^(1/power)
    original = threshold_alpha + np.sign(diff) * np.abs(diff) ** (1.0 / power)
    
    return original.item() if is_scalar else original


def plot_results(data=None, n=15, m=3, seed=0):
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3)
    
    if data is None:
        data = main(n=n, m=m, seed=seed)
    
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
    
    # Create rainbow colormap from ultraviolet (purple/violet) to infrared (red)
    # Colors: purple → blue → cyan → green → yellow → orange → red
    # Using muted tones (lower saturation and brightness) for eye comfort
    if len(perms) == 1:
        # Single permutation case
        colors_rainbow = ['#6B4C93']  # Muted purple/violet
    else:
        # Create a custom colormap from purple to red with muted colors
        # Using HSV space: purple (0.75) → blue (0.67) → cyan (0.5) → green (0.33) → yellow (0.17) → red (0.0)
        # Reduced saturation (0.7) and brightness (0.85) for softer, more comfortable colors
        n_colors = len(perms)
        hsv_values = np.linspace(0.75, 0.0, n_colors)  # From purple (0.75) to red (0.0), wrapping through the spectrum
        colors_rainbow = [mcolors.hsv_to_rgb([h, 0.7, 0.85]) for h in hsv_values]  # Saturation=0.7, Value=0.85
        # Convert to hex format
        colors_rainbow = [mcolors.rgb2hex(c) for c in colors_rainbow]
    
    # Create a ListedColormap from the rainbow colors
    cmap = mcolors.ListedColormap(colors_rainbow)
    bounds = np.arange(len(perms) + 1) - 0.5
    norm = mcolors.BoundaryNorm(bounds, len(perms))
    
    # Plot Heatmap
    im = ax_heat.imshow(
        strategies,
        aspect='auto',
        cmap=cmap,
        norm=norm,
        interpolation='nearest',
    )
    
    ax_heat.set_title(rf"Voter Strategy Evolution ($\alpha={data['heatmap']['alpha']:.3f}$)")
    ax_heat.set_xlabel("Time Step (t)")
    ax_heat.set_ylabel("Voter Index")
    ax_heat.set_yticks(range(strategies.shape[0]))
    
    # Custom Legend for Permutations
    perm_labels = [">".join(labels[c] for c in p) for p in perms]
    tick_locs = np.arange(len(perms))
    cbar = plt.colorbar(im, ax=ax_heat, ticks=tick_locs, boundaries=bounds)
    cbar.ax.set_yticklabels(perm_labels)
    cbar.ax.invert_yaxis()  # Put the first ranking at the top
    cbar.set_label("Reported Ranking")
    
    # C. Ternary Trajectories (Before and After Threshold)
    if ternary is not None and ternary.get("traj_before") is not None and ternary.get("traj_after") is not None:
        traj_before = ternary["traj_before"]
        traj_after = ternary["traj_after"]
        
        # Ternary Projection function
        def project(p_vec):
            x = 0.5 * p_vec[:, 0] + 1.0 * p_vec[:, 1]
            y = (np.sqrt(3) / 2) * p_vec[:, 0]
            return x, y
        
        # Plot Before Threshold
        ax_tern_before = fig.add_subplot(gs[1, 0])
        avg_traj_before = np.cumsum(traj_before, axis=0) / np.arange(1, len(traj_before) + 1)[:, None]
        
        tri_x = [0, 1, 0.5, 0]; tri_y = [0, 0, np.sqrt(3)/2, 0]
        ax_tern_before.plot(tri_x, tri_y, 'k-', lw=1)
        ax_tern_before.text(0.5, np.sqrt(3)/2 + 0.02, f'Cand {labels[0]}', ha='center')
        ax_tern_before.text(1.02, -0.05, f'Cand {labels[1]}', ha='center')
        ax_tern_before.text(-0.02, -0.05, f'Cand {labels[2]}', ha='center')
        
        ix_before, iy_before = project(traj_before)
        ax_tern_before.plot(ix_before, iy_before, 'gray', alpha=0.3, lw=0.5, label='Instantaneous $p^t$')
        
        ax_before, ay_before = project(avg_traj_before)
        ax_tern_before.plot(ax_before, ay_before, 'b-', lw=2, label='Running Avg')
        ax_tern_before.scatter(ax_before[0], ay_before[0], c='red', marker='x', s=100, label='Start', zorder=10)
        ax_tern_before.scatter(ax_before[-1], ay_before[-1], c='blue', marker='*', s=150, label='End (Avg)', zorder=10)
        
        # Show the precise alpha used (more decimals to distinguish close values)
        ax_tern_before.set_title(f"Before Threshold ($\\alpha={alpha_before:.3f}$)")
        ax_tern_before.axis('off')
        ax_tern_before.set_aspect('equal')
        
        # Plot After Threshold
        ax_tern_after = fig.add_subplot(gs[1, 1])
        avg_traj_after = np.cumsum(traj_after, axis=0) / np.arange(1, len(traj_after) + 1)[:, None]
        
        ax_tern_after.plot(tri_x, tri_y, 'k-', lw=1)
        ax_tern_after.text(0.5, np.sqrt(3)/2 + 0.02, f'Cand {labels[0]}', ha='center')
        ax_tern_after.text(1.02, -0.05, f'Cand {labels[1]}', ha='center')
        ax_tern_after.text(-0.02, -0.05, f'Cand {labels[2]}', ha='center')
        
        ix_after, iy_after = project(traj_after)
        ax_tern_after.plot(ix_after, iy_after, 'gray', alpha=0.3, lw=0.5, label='Instantaneous $p^t$')
        
        ax_after, ay_after = project(avg_traj_after)
        ax_tern_after.plot(ax_after, ay_after, 'b-', lw=2, label='Running Avg')
        ax_tern_after.scatter(ax_after[0], ay_after[0], c='red', marker='x', s=100, label='Start', zorder=10)
        ax_tern_after.scatter(ax_after[-1], ay_after[-1], c='blue', marker='*', s=150, label='End (Avg)', zorder=10)
        
        # Show the precise alpha used (more decimals to distinguish close values)
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
    plt.show()


def main(n=15, m=3, seed=0, baselines=None, plot=True):
    """
    Parameterized entry point returning simulation data.
    
    Args:
        n: Number of voters
        m: Number of candidates
        seed: Random seed for reproducibility
        baselines: Optional list of baseline permutation indices (length n), or None for random sampling
        plot: Whether to show plots (default True)
    
    Returns:
        Dictionary with simulation results
    """
    rng_phase = np.random.default_rng(seed)
    rng_heat = np.random.default_rng(seed + 1)

    alphas, dists = run_phase_transition(n=n, m=m, seed=seed, rng=rng_phase, baselines=baselines)
    threshold_alpha = compute_threshold_alpha(alphas, dists)
    alpha_before, alpha_after = find_before_after_alphas(alphas, threshold_alpha)
    if alpha_before is None or alpha_after is None:
        alpha_before = 0.05
        alpha_after = 0.60
        
    ternary = {"traj_before": None, "traj_after": None}

    # Use a very small alpha (near zero) for the heatmap to visualize rank changes
    # when there's minimal anchoring force
    alpha_heatmap = 0.001  # Very close to zero to minimize anchoring
    
    if m == 3:
        # Run heatmap with near-zero alpha to see if ranks change
        strategies, perms, traj_heatmap = run_full_scenario_for_alpha(
            alpha_heatmap, n=n, m=m, eta=0.2, beta=3.0, T=300, seed=seed, rng=rng_heat, baselines=baselines
        )
        
        # Ternary plots still use before/after threshold alphas
        if alpha_before is not None:
            traj_before = run_phase_transition_ternary(
                alpha_before, T=300, n=n, m=m, eta=0.2, beta=3.0, seed=seed, rng=None, baselines=baselines
            )
            ternary["traj_before"] = traj_before
        if alpha_after is not None:
            traj_after = run_phase_transition_ternary(
                alpha_after, T=300, n=n, m=m, eta=0.2, beta=3.0, seed=seed, rng=None, baselines=baselines
            )
            ternary["traj_after"] = traj_after
    else:
        # Fallback: keep previous behavior for non-ternary cases
        strategies, perms, traj_heatmap = run_heatmap_scenario(n=n, m=m, seed=seed, rng=rng_heat, baselines=baselines)
        ternary = {"traj_before": None, "traj_after": None}
    
    results = {
        "alphas": alphas,
        "dists": dists,
        "threshold_alpha": threshold_alpha,
        "alpha_before": alpha_before,
        "alpha_after": alpha_after,
        "heatmap": {
            "strategies": strategies,
            "perms": perms,
            "traj": traj_heatmap,
            "alpha": alpha_heatmap,
        },
        "ternary": ternary,
    }
    
    if plot:
        plot_results(data=results, n=n, m=m, seed=seed)
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run iterative voting system simulation with phase transition analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default run (n=15, m=3, seed=0, with plotting)
  uv run python examples/heatmap.py
  
  # Custom parameters
  uv run python examples/heatmap.py --n 20 --m 4 --seed 42
  
  # With explicit baselines (old syntax: comma-separated)
  uv run python examples/heatmap.py --n 6 --m 3 --baselines "0,1,2,0,1,2"
  
  # With explicit baselines (new syntax: repetition, n inferred)
  uv run python examples/heatmap.py --m 3 --baselines "0*5,3*5,4*5"
  
  # Run without plotting
  uv run python examples/heatmap.py --no-plot
        """
    )
    parser.add_argument("--n", type=int, default=None, 
                       help="Number of voters (default: 15, or inferred from --baselines if provided)")
    parser.add_argument("--m", type=int, default=3, 
                       help="Number of candidates (default: 3, required to validate baseline indices)")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for reproducibility (default: 0)")
    parser.add_argument("--baselines", type=str, default=None, 
                       help="Baseline permutation indices. Supports two formats:\n"
                            "  - Old: comma-separated indices (e.g., '0,1,2,0,1,2')\n"
                            "  - New: repetition syntax (e.g., '0*5,3*5,4*5' for 5 voters each)\n"
                            "If provided, n will be inferred from the total count. If not provided, baselines are sampled uniformly.")
    parser.add_argument("--no-plot", action="store_true", 
                       help="Disable plotting (default: plotting is enabled)")
    
    args = parser.parse_args()
    
    # Parse baselines if provided, otherwise use defaults
    if args.baselines:
        baselines, inferred_n = parse_baselines(args.baselines, args.m, args.n)
        # Use inferred n if n was not explicitly provided
        n = inferred_n if args.n is None else args.n
        # Double-check they match
        if args.n is not None and inferred_n != args.n:
            parser.error(f"Number of voters from --baselines ({inferred_n}) doesn't match --n ({args.n})")
    else:
        baselines = None
        n = args.n if args.n is not None else 15
    
    # Run main with plotting enabled by default (unless --no-plot is set)
    results = main(n=n, m=args.m, seed=args.seed, baselines=baselines, plot=not args.no_plot)
    
    if not args.no_plot:
        print("Run complete. Plots displayed.")
    else:
        print("Run complete. Results dictionary keys:", list(results.keys()))