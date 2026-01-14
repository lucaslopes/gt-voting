"""Plot probability distributions as stacked area charts (proportion plots)."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import json
import os
from core.aggregator_core import aggregate_rankings
from core.rankings_core import generate_rankings, candidate_labels
from plots.BasePlot import BasePlot



class ProportionsPlot(BasePlot):
    """Plot probability distributions as stacked area charts."""
    
    def plot(self, reported_rankings_or_strategies, m=None, all_rankings=None,
             labels=None, mechanism="pairwise_majority", ax=None, title=None,
             show_integers=False, use_time_average=False, p_history=None,
             p_avg_history=None):
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
            fig, ax = plt.subplots(figsize=self.PLOT_FIGSIZE)
    
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
                # Use p_history directly when provided to ensure consistency with phase transition plot
                # p_history contains probabilities from GT mechanism (via sys.step()), which matches
                # the mechanism used in phase transition calculations
                # p_history has shape [T, m] for t=0..T-1 (or t=1..T depending on source)
                # We need to match the number of time steps in strategies
                if p_history.shape[0] == n_timesteps:
                    # Direct match: use p_history as-is
                    probabilities_over_time = p_history.tolist()
                    time_steps = list(range(n_timesteps))
                    use_precomputed = True
                elif p_history.shape[0] == n_timesteps - 1:
                    # p_history might be missing t=0, compute it from strategies and prepend
                    rankings_at_t0 = [all_rankings[strategies[i, 0]] for i in range(n_voters)]
                    probs_t0 = aggregate_rankings(rankings_at_t0, mechanism=mechanism)
                    probabilities_over_time = [probs_t0] + p_history.tolist()
                    time_steps = list(range(n_timesteps))
                    use_precomputed = True
                else:
                    # Shape mismatch: fall back to computing from strategies
                    use_precomputed = False
            
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
        
        use_integers, _ = self.prepare_labels([sample_ranking], labels)
        
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
        
        # Create colors for candidates using tab10 colormap
        # Map: A -> tab10 orange (index 1), B -> tab10 brown (index 5), C -> tab10 pink (index 6)
        tab10_cmap = plt.cm.get_cmap('tab10')
        colors = []
        for i, label in enumerate(legend_labels):
            # Map candidate label to tab10 color index
            if label == 'A':
                color_idx = 5  # tab10 brown
            elif label == 'B':
                color_idx = 1  # tab10 orange
            elif label == 'C':
                color_idx = 6  # tab10 pink
            else:
                # For additional candidates, use default colormap
                color_idx = i % 10
            colors.append(tab10_cmap(color_idx))
        
        # Use stacked bar chart for both single election and strategic reports
        if is_strategic_reports:
            # Create stacked bar chart for multiple time steps
            for t_idx, t in enumerate(x_axis):
                probs = prob_array[t_idx]  # Probabilities for this time step
                bottom = 0
                # Plot candidates in reverse order so that the last candidate
                # (e.g., C) is closest to the x-axis and the first (e.g., A) is on top
                for i in reversed(range(m)):
                    bar_height = probs[i]
                    # Do not pass labels here; we construct a custom legend below
                    ax.bar(t, bar_height, bottom=bottom, color=colors[i], alpha=0.7, edgecolor='none', linewidth=0, width=1.0)
                    bottom += bar_height
        else:
            # Create stacked bar chart for single election
            probs = prob_array[0]  # Single row of probabilities
            bottom = 0
            # Plot candidates in reverse order so that the last candidate
            # (e.g., C) is closest to the x-axis and the first (e.g., A) is on top
            for i in reversed(range(m)):
                # Do not pass labels here; we construct a custom legend below
                ax.bar(0, probs[i], bottom=bottom, color=colors[i], alpha=0.7, edgecolor='none', linewidth=0)
                bottom += probs[i]
        
        # Configure axes
        ax.set_xlabel(x_label, fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax.set_ylabel("Probability", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax.set_ylim(0, 1)
        ax.tick_params(axis='both', which='major', labelsize=self.PLOT_TICK_LABELSIZE)
        
        # Set x-axis ticks and limits (with proper padding for bars)
        if is_strategic_reports:
            # Set x-axis ticks with evenly spaced labels to avoid overlap
            # Use a reasonable number of ticks (5-10) based on the number of time steps
            # Always include t=0 and t=T-1
            n_timesteps = len(x_axis)
            if n_timesteps <= 10:
                # For small numbers, show all ticks
                x_ticks = x_axis.tolist()
            else:
                # For larger numbers, use 6-8 evenly spaced ticks
                n_ticks = min(8, max(6, n_timesteps // 50))
                # Generate evenly spaced tick positions
                x_ticks = np.linspace(x_axis[0], x_axis[-1], n_ticks, dtype=int)
                # Ensure we have t=0 and last time step
                if x_ticks[0] != x_axis[0]:
                    x_ticks[0] = int(x_axis[0])
                if x_ticks[-1] != x_axis[-1]:
                    x_ticks[-1] = int(x_axis[-1])
                # Remove duplicates while preserving order
                x_ticks = list(dict.fromkeys(x_ticks))
            
            ax.set_xticks(x_ticks)
            # Set x-axis limits with padding to show full bars
            # Bars have width=1.0 and are centered on time steps, so they extend ±0.5
            # Add padding of 0.5 on each side to show full bars
            x_min = x_axis[0] - 0.5
            x_max = x_axis[-1] + 0.5
            ax.set_xlim(x_min, x_max)
        else:
            ax.set_xticks([0])
            ax.set_xticklabels(["Election"])
            # For single election, set tight limits around the single point
            ax.set_xlim(-0.05, 0.05)
        
        # Grid disabled
        ax.grid(False)
        
        # Build explicit legend proxy patches so colors are independent of bar drawing order.
        legend_patches = [
            Patch(facecolor=colors[i], edgecolor="none", label=legend_labels[i])
            for i in range(m)
        ]

        ax.legend(
            handles=legend_patches,
            labels=legend_labels,
            # Slightly outside the right edge and a bit below the top for nicer spacing.
            bbox_to_anchor=(1.03, 1.035),
            loc="upper left",
            title="Candidates",
            framealpha=0.9,
            fontsize=self.PLOT_LEGEND_FONTSIZE,
            borderpad=0.8,
            columnspacing=2.0,
            handlelength=2.6,
            handletextpad=0.8,
        )
        
        # Set title
        if title is None:
            if is_strategic_reports:
                outcome_type = "Time-Averaged" if use_time_average else "Instantaneous"
                ax.set_title(
                    f"{outcome_type} Probability Distribution Evolution\n({n_voters} voters, {m} candidates, {len(time_steps)} time steps)",
                    fontsize=self.PLOT_TITLE_FONTSIZE,
                    fontweight='bold',
                    pad=self.PLOT_TITLE_PAD
                )
            else:
                ax.set_title(
                    f"Probability Distribution\n({len(reported_rankings)} voters, {m} candidates)",
                    fontsize=self.PLOT_TITLE_FONTSIZE,
                    fontweight='bold',
                    pad=self.PLOT_TITLE_PAD
                )
        else:
            ax.set_title(title, fontsize=self.PLOT_TITLE_FONTSIZE, fontweight='bold', pad=self.PLOT_TITLE_PAD)
        
        # Adjust layout to ensure legend is visible when placed outside
        fig = ax.figure
        fig.tight_layout()
        
        return ax


# Backward compatibility wrapper
def plot_proportions(*args, **kwargs):
    """Backward compatibility wrapper for plot_proportions function."""
    plotter = ProportionsPlot()
    return plotter.plot(*args, **kwargs)
