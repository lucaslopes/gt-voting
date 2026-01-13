"""Plot probability distributions as stacked area charts (proportion plots)."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import json
import os
from core.aggregator_core import aggregate_rankings
from core.rankings_core import generate_rankings, candidate_labels
from plots.plot_utils import (
    prepare_labels,
    PLOT_FIGSIZE,
    PLOT_TITLE_FONTSIZE,
    PLOT_TITLE_PAD,
    PLOT_AXIS_LABEL_FONTSIZE,
    PLOT_TICK_LABELSIZE,
    PLOT_LEGEND_FONTSIZE,
)



def plot_proportions(
    reported_rankings_or_strategies,
    m=None,
    all_rankings=None,
    labels=None,
    mechanism="pairwise_majority",
    ax=None,
    title=None,
    show_integers=False,
    use_time_average=False,
    p_history=None,
    p_avg_history=None
):
    """
    Plot probability distributions as a stacked area chart (proportion plot).
    
    This function visualizes how candidate probabilities evolve over time. It can handle:
    - Single election: List of rankings (one time step)
    - Multiple time steps: Strategic reports array [voters, T+1] where each cell is a ranking index
    
    Args:
        reported_rankings_or_strategies: Either:
            - List of ranking tuples for single election (e.g., [(0,1,2), (1,0,2), ...])
            - numpy array of shape [voters, T+1] where each cell is a ranking index (for strategic reports)
        m: Number of candidates (required if all_rankings is None and input is strategic reports array)
        all_rankings: List of all possible ranking tuples (required if input is strategic reports array)
        labels: Optional list of candidate labels. If None, will generate A, B, C, etc.
        mechanism: Aggregation mechanism name (default: "pairwise_majority")
        ax: Optional matplotlib axes. If None, creates a new figure.
        title: Optional title for the plot. If None, uses default title.
        show_integers: If True and candidates are integers, display them as integers in legend
        use_time_average: If True and p_avg_history is provided, plot time-averaged outcomes \\hat{p}^t
                         instead of instantaneous outcomes p^t (default: False)
        p_history: Optional numpy array of shape [T, m] containing instantaneous outcomes p^t.
                    If provided and use_time_average=False, will be used directly instead of computing
                    from strategies. Only used for strategic reports mode.
        p_avg_history: Optional numpy array of shape [T, m] containing time-averaged outcomes \\hat{p}^t.
                       If provided and use_time_average=True, will be used directly. Only used for
                       strategic reports mode.
    
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
        
        >>> # With time-averaged outcomes
        >>> plot_proportions(strategies, m=3, all_rankings=all_rankings, 
        ...                  use_time_average=True, p_avg_history=p_avg_history)
    """
    # Initialize figure if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=PLOT_FIGSIZE)
    
    # Determine if input is single election (list) or strategic reports (array)
    is_strategic_reports = isinstance(reported_rankings_or_strategies, np.ndarray)
    
    if is_strategic_reports:
        # Strategic reports: array of shape [voters, T+1] with ranking indices
        strategies = reported_rankings_or_strategies
        
        if strategies.ndim != 2:
            raise ValueError(f"strategies must be 2D array [voters, T+1], got shape {strategies.shape}")
        
        n_voters, n_timesteps = strategies.shape
        
        if all_rankings is None:
            if m is None:
                raise ValueError("Either m or all_rankings must be provided when using strategic reports")
            all_rankings = generate_rankings(m, alphabetical=False)
        
        # Extract candidates from first ranking
        first_ranking = all_rankings[0]
        candidates = list(first_ranking)
        m = len(candidates)
        
        # Determine if we should use precomputed outcomes or compute from strategies
        use_precomputed = False
        if use_time_average and p_avg_history is not None:
            # p_avg_history is computed with GT mechanism during strategy evolution
            # If user wants GT mechanism, we can use p_avg_history directly (more efficient)
            # Otherwise, we need to recompute from strategies using the user's mechanism
            if mechanism.upper() == "GT":
                # Use precomputed time-averaged outcomes (computed with GT mechanism)
                # p_avg_history has shape [T, m] for t=1..T (doesn't include t=0)
                # We need to compute t=0 from strategies and prepend it
                rankings_at_t0 = [all_rankings[strategies[i, 0]] for i in range(n_voters)]
                probs_t0 = aggregate_rankings(rankings_at_t0, mechanism=mechanism)
                # Prepend t=0 to p_avg_history
                probabilities_over_time = [probs_t0] + p_avg_history.tolist()
                # Time steps: t=0 to t=T (where T is the last index in p_avg_history)
                time_steps = list(range(len(probabilities_over_time)))
                use_precomputed = True
            else:
                # User wants different mechanism, so compute time-averaged outcomes from strategies
                time_steps = []
                probabilities_over_time = []
                p_sum = np.zeros(m, dtype=float)  # Accumulator for time-averaging
                
                # Start from t=0
                for t in range(n_timesteps):
                    # Extract rankings for this time step
                    rankings_at_t = [all_rankings[strategies[i, t]] for i in range(n_voters)]
                    
                    # Aggregate to get probabilities using user's specified mechanism
                    probs = aggregate_rankings(rankings_at_t, mechanism=mechanism)
                    probs_array = np.array(probs)
                    
                    
                    if t == 0:
                        # For t=0, just use the instantaneous outcome (no averaging yet)
                        probabilities_over_time.append(probs_array)
                        time_steps.append(t)
                    else:
                        # For t>=1, accumulate and compute time-averaged outcome
                        # \hat{p}^t = (1/t) * sum_{tau=1}^t p^tau
                        p_sum += probs_array
                        p_avg = p_sum / t
                        probabilities_over_time.append(p_avg)
                        time_steps.append(t)
                
                use_precomputed = True
            
            # Mark as precomputed to avoid falling through to the non-precomputed path
            use_precomputed = True
        elif not use_time_average and p_history is not None:
            # NOTE: p_history contains probabilities from SAMPLED rankings during evolution,
            # but the console prints probabilities from MOST LIKELY rankings (argmax).
            # To match the console output, we should compute from strategies (most likely rankings)
            # instead of using p_history. So we fall through to compute from strategies.
            # NOTE: p_history contains probabilities from SAMPLED rankings during evolution,
            # but the console prints probabilities from MOST LIKELY rankings (argmax).
            # To match the console output, we should compute from strategies (most likely rankings)
            # instead of using p_history. So we fall through to compute from strategies.
            use_precomputed = False  # Force computation from strategies to match console output
        
        if not use_precomputed:
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
        probabilities_over_time = [probs]
        x_axis = np.array([0])  # Single time point
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
    # Shape: [n_timesteps, candidates]
    prob_array = np.array(probabilities_over_time)
    
    # Create colors for candidates (using rainbow colormap)
    colors = create_candidate_colormap(m)
    
    # Use stacked bar chart for both single election and strategic reports
    if is_strategic_reports:
        # Create stacked bar chart for multiple time steps
        for t_idx, t in enumerate(x_axis):
            probs = prob_array[t_idx]  # Probabilities for this time step
            bottom = 0
            for i in range(m):
                # Only add label for first time step to avoid duplicate legend entries
                label = legend_labels[i] if t_idx == 0 else None
                bar_height = probs[i]
                ax.bar(t, bar_height, bottom=bottom, label=label, color=colors[i], alpha=0.7, edgecolor='white', linewidth=0.5)
                bottom += bar_height
    else:
        # Create stacked bar chart for single election
        probs = prob_array[0]  # Single row of probabilities
        bottom = 0
        for i in range(m):
            ax.bar(0, probs[i], bottom=bottom, label=legend_labels[i], color=colors[i], alpha=0.7, edgecolor='white', linewidth=0.5)
            bottom += probs[i]
    
    # Configure axes
    ax.set_xlabel(x_label, fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax.set_ylabel("Probability", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax.set_ylim(0, 1)
    ax.tick_params(axis='both', which='major', labelsize=PLOT_TICK_LABELSIZE)
    
    # Set x-axis ticks and limits (with proper padding for bars)
    if is_strategic_reports:
        ax.set_xticks(x_axis)
        # Set x-axis limits with padding to show full bars
        # Bars are centered on time steps, default width is 0.8, so they extend ±0.4
        # Add padding of 0.5 on each side to show full bars
        x_min = x_axis[0] - 0.5
        x_max = x_axis[-1] + 0.5
        ax.set_xlim(x_min, x_max)
    else:
        ax.set_xticks([0])
        ax.set_xticklabels(["Election"])
        # For single election, set tight limits around the single point
        ax.set_xlim(-0.05, 0.05)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add legend outside the plot area
    ax.legend(bbox_to_anchor=(1.0, 1.0), loc='upper left', framealpha=0.9, fontsize=PLOT_LEGEND_FONTSIZE)
    
    # Set title
    if title is None:
        if is_strategic_reports:
            outcome_type = "Time-Averaged" if use_time_average else "Instantaneous"
            ax.set_title(
                f"{outcome_type} Probability Distribution Evolution\n({n_voters} voters, {m} candidates, {len(time_steps)} time steps)",
                fontsize=PLOT_TITLE_FONTSIZE,
                fontweight='bold',
                pad=PLOT_TITLE_PAD
            )
        else:
            ax.set_title(
                f"Probability Distribution\n({len(reported_rankings)} voters, {m} candidates)",
                fontsize=PLOT_TITLE_FONTSIZE,
                fontweight='bold',
                pad=PLOT_TITLE_PAD
            )
    else:
        ax.set_title(title, fontsize=PLOT_TITLE_FONTSIZE, fontweight='bold', pad=PLOT_TITLE_PAD)
    
    # Adjust layout to ensure legend is visible when placed outside
    fig = ax.figure
    fig.tight_layout()
    
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
