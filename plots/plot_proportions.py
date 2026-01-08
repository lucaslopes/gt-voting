"""Plot probability distributions as stacked area charts (proportion plots)."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import json
import os
from core.aggregator_core import aggregate_rankings
from core.rankings_core import generate_rankings, candidate_labels
from plots.plot_utils import prepare_labels

# #region agent log
def _debug_log(location, message, data, hypothesis_id):
    try:
        log_path = "/Users/lucas/Code/gt-voting/.cursor/debug.log"
        with open(log_path, "a") as f:
            f.write(json.dumps({"location": location, "message": message, "data": data, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": hypothesis_id}) + "\n")
    except: pass
# #endregion


def plot_proportions(
    reported_rankings_or_strategies,
    m=None,
    all_rankings=None,
    labels=None,
    mechanism="pairwise_majority",
    ax=None,
    title=None,
    show_integers=False
):
    """
    Plot probability distributions as a stacked area chart (proportion plot).
    
    This function visualizes how candidate probabilities evolve over time. It can handle:
    - Single election: List of rankings (one time step)
    - Multiple time steps: Strategic reports array [n, T+1] where each cell is a ranking index
    
    Args:
        reported_rankings_or_strategies: Either:
            - List of ranking tuples for single election (e.g., [(0,1,2), (1,0,2), ...])
            - numpy array of shape [n, T+1] where each cell is a ranking index (for strategic reports)
        m: Number of candidates (required if all_rankings is None and input is strategic reports array)
        all_rankings: List of all possible ranking tuples (required if input is strategic reports array)
        labels: Optional list of candidate labels. If None, will generate A, B, C, etc.
        mechanism: Aggregation mechanism name (default: "pairwise_majority")
        ax: Optional matplotlib axes. If None, creates a new figure.
        title: Optional title for the plot. If None, uses default title.
        show_integers: If True and candidates are integers, display them as integers in legend
    
    Returns:
        The matplotlib axes object containing the plot
    
    Example:
        >>> # Single election
        >>> rankings = [(0, 1, 2), (0, 1, 2), (1, 0, 2)]
        >>> plot_proportions(rankings, m=3)
        
        >>> # Strategic reports over T iterations
        >>> strategies = np.array([[0, 1, 2], [1, 0, 2]])  # 2 voters, 3 time steps
        >>> all_rankings = generate_rankings(3)
        >>> plot_proportions(strategies, m=3, all_rankings=all_rankings)
    """
    # Initialize figure if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    
    # Determine if input is single election (list) or strategic reports (array)
    is_strategic_reports = isinstance(reported_rankings_or_strategies, np.ndarray)
    
    if is_strategic_reports:
        # Strategic reports: array of shape [n, T+1] with ranking indices
        strategies = reported_rankings_or_strategies
        
        if strategies.ndim != 2:
            raise ValueError(f"strategies must be 2D array [n, T+1], got shape {strategies.shape}")
        
        n_voters, n_timesteps = strategies.shape
        
        if all_rankings is None:
            if m is None:
                raise ValueError("Either m or all_rankings must be provided when using strategic reports")
            all_rankings = generate_rankings(m, alphabetical=False)
        
        # Extract candidates from first ranking
        first_ranking = all_rankings[0]
        candidates = list(first_ranking)
        m = len(candidates)
        
        # For each time step, extract rankings and aggregate
        time_steps = []
        probabilities_over_time = []
        
        for t in range(n_timesteps):
            # Extract rankings for this time step
            rankings_at_t = [all_rankings[strategies[i, t]] for i in range(n_voters)]
            
            # Aggregate to get probabilities
            probs = aggregate_rankings(rankings_at_t, mechanism=mechanism)
            probabilities_over_time.append(probs)
            time_steps.append(t)
        
        x_axis = np.array(time_steps)
        x_label = "Time Step (t)"
        
    else:
        # Single election: list of rankings
        reported_rankings = reported_rankings_or_strategies
        
        if not reported_rankings:
            raise ValueError("reported_rankings cannot be empty")
        
        # Extract candidates from first ranking
        first_ranking = reported_rankings[0]
        candidates = list(first_ranking)
        m = len(candidates)
        
        # Aggregate to get probabilities
        probs = aggregate_rankings(reported_rankings, mechanism=mechanism)
        _debug_log("plot_proportions.py:109", "Single election probs calculated", {"probs": probs.tolist() if hasattr(probs, 'tolist') else list(probs), "len": len(probs)}, "H3")
        probabilities_over_time = [probs]
        x_axis = np.array([0])  # Single time point
        _debug_log("plot_proportions.py:111", "Single election x_axis", {"x_axis": x_axis.tolist(), "shape": x_axis.shape}, "H2")
        x_label = "Election"
    
    # Prepare labels
    # Use the first ranking to determine label type
    if is_strategic_reports:
        sample_ranking = all_rankings[strategies[0, 0]]
    else:
        sample_ranking = reported_rankings[0]
    
    use_integers, _ = prepare_labels([sample_ranking], labels)
    
    # Get candidate labels
    if labels is None:
        if use_integers:
            candidate_labels_list = candidate_labels(m)
        else:
            candidate_labels_list = sorted(list(set(candidates)))
    else:
        candidate_labels_list = labels
    
    # Create candidate labels for legend
    if show_integers:
        # Show integers even if we have labels
        legend_labels = [str(c) for c in candidates]
    elif use_integers:
        # Map candidate indices to alphabetical labels
        legend_labels = [candidate_labels_list[c] for c in candidates]
    else:
        # Candidates are already strings/labels
        legend_labels = [str(c) for c in candidates]
    
    # Convert probabilities_over_time to numpy array for easier manipulation
    # Shape: [n_timesteps, m]
    prob_array = np.array(probabilities_over_time)
    _debug_log("plot_proportions.py:144", "Prob array before plotting", {"prob_array": prob_array.tolist(), "shape": prob_array.shape, "x_axis": x_axis.tolist(), "is_strategic": is_strategic_reports}, "H3")
    
    # Create colors for candidates (using rainbow colormap)
    colors = create_candidate_colormap(m)
    _debug_log("plot_proportions.py:147", "Colors created", {"colors": colors, "m": m}, "H5")
    
    # For single election, use stacked bar chart; for strategic reports, use stacked area chart
    if is_strategic_reports:
        # Create stacked area chart for multiple time steps
        stackplot_data = [prob_array[:, i] for i in range(m)]
        _debug_log("plot_proportions.py:152", "Stackplot data prepared", {"num_series": len(stackplot_data), "series_lengths": [len(s) for s in stackplot_data]}, "H2")
        ax.stackplot(
            x_axis,
            *stackplot_data,
            labels=legend_labels,
            colors=colors,
            alpha=0.7,
            edgecolors='white',
            linewidths=0.5
        )
        _debug_log("plot_proportions.py:159", "Stackplot called", {"x_axis_len": len(x_axis)}, "H2")
    else:
        # Create stacked bar chart for single election
        probs = prob_array[0]  # Single row of probabilities
        _debug_log("plot_proportions.py:163", "Single election bar chart", {"probs": probs.tolist(), "x_pos": 0}, "H2")
        bottom = 0
        for i in range(m):
            ax.bar(0, probs[i], bottom=bottom, label=legend_labels[i], color=colors[i], alpha=0.7, edgecolor='white', linewidth=0.5)
            bottom += probs[i]
        _debug_log("plot_proportions.py:168", "Bar chart created", {"bars_created": m}, "H2")
    
    # Configure axes
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel("Probability", fontsize=12)
    ax.set_ylim(0, 1)
    
    # Set x-axis ticks and limits (tight from 0 to T)
    if is_strategic_reports:
        ax.set_xticks(x_axis)
        # Set tight x-axis limits from 0 to T (last time step)
        ax.set_xlim(0, x_axis[-1])
    else:
        ax.set_xticks([0])
        ax.set_xticklabels(["Election"])
        # For single election, set tight limits around the single point
        ax.set_xlim(-0.05, 0.05)
        _debug_log("plot_proportions.py:175", "Single election xlim set", {"xlim": ax.get_xlim(), "x_axis": x_axis.tolist()}, "H1")
        _debug_log("plot_proportions.py:175", "Single election ylim", {"ylim": ax.get_ylim()}, "H4")
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add legend
    ax.legend(loc='upper right', framealpha=0.9, fontsize=10)
    
    # Final axis state check
    _debug_log("plot_proportions.py:180", "Final axis state", {"xlim": ax.get_xlim(), "ylim": ax.get_ylim(), "has_data": len(ax.patches) > 0 or len(ax.collections) > 0, "patches": len(ax.patches), "collections": len(ax.collections)}, "H4")
    
    # Set title
    if title is None:
        if is_strategic_reports:
            ax.set_title(
                f"Probability Distribution Evolution ({n_voters} voters, {m} candidates, {n_timesteps} time steps)",
                fontsize=14,
                fontweight='bold',
                pad=20
            )
        else:
            ax.set_title(
                f"Probability Distribution ({len(reported_rankings)} voters, {m} candidates)",
                fontsize=14,
                fontweight='bold',
                pad=20
            )
    else:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    return ax


def create_candidate_colormap(m):
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
