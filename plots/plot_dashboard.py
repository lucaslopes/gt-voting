"""Dashboard plotting function for combined 2×2 grid view (4 quadrants)."""

import numpy as np
import matplotlib.pyplot as plt
from core.rankings_core import candidate_labels
from core.phase_transition import warp_alpha_axis
from plots.plot_voter_strategies import plot_voter_strategies
from plots.plot_ternary import _project_ternary
from plots.plot_proportions import plot_proportions
from plots.BasePlot import BasePlot


class DashboardPlot(BasePlot):
    """Dashboard plotting for combined 2×2 grid view (4 quadrants)."""
    
    def plot(self, data, n=15, m=3, seed=0):
        """
        Create combined dashboard with 2×2 grid layout (4 quadrants, 16:9 aspect ratio).
        
        The dashboard includes:
        - Phase transition plot (top left quadrant)
        - Voter Strategy Evolution (top right quadrant)
        - Ternary plots before/after threshold (bottom left quadrant, side by side)
        - Probability Distribution Evolution (bottom right quadrant)
        
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
        fig = plt.figure(figsize=(16, 9))
        # Create 2×2 grid for 4 quadrants
        # Set spacing parameters from manual adjustment
        gs = fig.add_gridspec(2, 2, hspace=0.6, wspace=0.24)
        
        alphas = data["alphas"]
        dists = data["dists"]
        threshold_alpha = data["threshold_alpha"]
        alpha_before = data["alpha_before"]
        alpha_after = data["alpha_after"]
        
        # #region agent log
        with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
            f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"K","location":"plot_dashboard.py:51","message":"Plot function received values","data":{{"threshold_alpha":{threshold_alpha},"alpha_before":{alpha_before},"alpha_after":{alpha_after},"alpha_before_rounded":{round(alpha_before, 3) if alpha_before is not None else None},"alpha_after_rounded":{round(alpha_after, 3) if alpha_after is not None else None},"threshold_rounded":{round(threshold_alpha, 3) if threshold_alpha is not None else None}}}}}\n')
        # #endregion
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
                             label=f'Threshold α≈{threshold_alpha:.3f}')
        
        ax_phase.set_title(f"(a) Phase Transition: Anchoring vs. Fairness", fontsize=self.PLOT_TITLE_FONTSIZE, fontweight='bold', pad=self.PLOT_TITLE_PAD)
        ax_phase.set_xlabel(r"Anchoring Parameter ($\alpha$)", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax_phase.set_ylabel("Distance of Outcome\nfrom Center (Tie)", fontsize=self.PLOT_AXIS_LABEL_FONTSIZE)
        ax_phase.grid(True, alpha=0.3)
        ax_phase.legend(fontsize=self.PLOT_LEGEND_FONTSIZE)
        ax_phase.tick_params(axis='both', which='major', labelsize=self.PLOT_TICK_LABELSIZE)
        
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
        
        # B. Strategy Heatmap (Top Right Quadrant)
        ax_heat = fig.add_subplot(gs[0, 1])
        plot_voter_strategies(
            strategies,
            perms,
            labels=labels,
            ax=ax_heat,
            title=rf"(d) Voter Strategy Evolution $\alpha={data['heatmap']['alpha']:.3f}$",
            title_fontsize=self.PLOT_TITLE_FONTSIZE
        )
        
        # C. Ternary Trajectories (Before and After Threshold) - Bottom Left Quadrant
        if ternary is not None and ternary.get("traj_before") is not None and ternary.get("traj_after") is not None:
            traj_before = ternary["traj_before"]
            traj_after = ternary["traj_after"]
            T = len(traj_before)
            
            # Create nested grid for two ternary plots in bottom-left quadrant
            # Use more vertical space by adjusting hspace and reducing bottom padding
            gs_ternary = gs[1, 0].subgridspec(1, 2, hspace=0.3, wspace=0.3)
            
            # Plot Before Threshold
            ax_tern_before = fig.add_subplot(gs_ternary[0, 0])
            avg_traj_before = np.cumsum(traj_before, axis=0) / np.arange(1, T + 1)[:, None]
            
            tri_x = [0, 1, 0.5, 0]
            tri_y = [0, 0, np.sqrt(3)/2, 0]
            ax_tern_before.plot(tri_x, tri_y, 'k-', lw=1)
            # Labels will be repositioned after setting axes limits
            
            ix_before, iy_before = _project_ternary(traj_before)
            ax_tern_before.plot(ix_before, iy_before, 'gray', alpha=0.3, lw=0.5, label='Instantaneous $p^t$')
            
            ax_before, ay_before = _project_ternary(avg_traj_before)
            ax_tern_before.plot(ax_before, ay_before, 'b-', lw=2, label='Running Avg')
            ax_tern_before.scatter(ax_before[0], ay_before[0], c='red', marker='x', s=100, label='Start', zorder=10)
            ax_tern_before.scatter(ax_before[-1], ay_before[-1], c='blue', marker='*', s=150, label='End (Avg)', zorder=10)
            
            # #region agent log
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                title_before = f"(b) Before Threshold\n$\\alpha={alpha_before:.3f}$"
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"L","location":"plot_dashboard.py:136","message":"Setting before threshold title","data":{{"alpha_before":{alpha_before},"alpha_before_rounded":{round(alpha_before, 3) if alpha_before is not None else None},"title":{repr(title_before)}}}}}\n')
            # #endregion
            ax_tern_before.set_title(f"(b) Before Threshold\n$\\alpha={alpha_before:.3f}$", 
                                    fontsize=self.PLOT_TITLE_FONTSIZE, pad=20, fontweight='bold')
            ax_tern_before.axis('off')
            ax_tern_before.set_aspect('equal')
            
            # Plot After Threshold
            ax_tern_after = fig.add_subplot(gs_ternary[0, 1])
            avg_traj_after = np.cumsum(traj_after, axis=0) / np.arange(1, T + 1)[:, None]
            
            ax_tern_after.plot(tri_x, tri_y, 'k-', lw=1)
            # Labels will be repositioned after setting axes limits
            
            ix_after, iy_after = _project_ternary(traj_after)
            ax_tern_after.plot(ix_after, iy_after, 'gray', alpha=0.3, lw=0.5, label='Instantaneous $p^t$')
            
            ax_after, ay_after = _project_ternary(avg_traj_after)
            ax_tern_after.plot(ax_after, ay_after, 'b-', lw=2, label='Running Avg')
            ax_tern_after.scatter(ax_after[0], ay_after[0], c='red', marker='x', s=100, label='Start', zorder=10)
            ax_tern_after.scatter(ax_after[-1], ay_after[-1], c='blue', marker='*', s=150, label='End (Avg)', zorder=10)
            
            # #region agent log
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                title_after = f"(c) After Threshold\n$\\alpha={alpha_after:.3f}$"
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"M","location":"plot_dashboard.py:156","message":"Setting after threshold title","data":{{"alpha_after":{alpha_after},"alpha_after_rounded":{round(alpha_after, 3) if alpha_after is not None else None},"threshold_alpha":{threshold_alpha},"threshold_rounded":{round(threshold_alpha, 3) if threshold_alpha is not None else None},"title":{repr(title_after)}}}}}\n')
            # #endregion
            ax_tern_after.set_title(f"(c) After Threshold\n$\\alpha={alpha_after:.3f}$", 
                                   fontsize=self.PLOT_TITLE_FONTSIZE, pad=20, fontweight='bold')
            ax_tern_after.axis('off')
            ax_tern_after.set_aspect('equal')
            
            # Get legend handles and labels from either plot (they're the same)
            handles, labels_legend = ax_tern_before.get_legend_handles_labels()
            
            # Set explicit axes limits to tightly bound the triangles and use more vertical space
            sqrt3_half = np.sqrt(3) / 2
            # Calculate padding to accommodate labels
            x_pad = 0.12
            y_pad_top = 0.15  # Extra space for top label and title
            y_pad_bottom = 0.12  # Extra space for bottom labels
            
            ax_tern_before.set_xlim(-x_pad, 1 + x_pad)
            ax_tern_before.set_ylim(-y_pad_bottom, sqrt3_half + y_pad_top)
            
            ax_tern_after.set_xlim(-x_pad, 1 + x_pad)
            ax_tern_after.set_ylim(-y_pad_bottom, sqrt3_half + y_pad_top)
            
            # Reposition labels to avoid overlap
            # Top label: move further up to avoid title overlap
            ax_tern_before.text(0.5, sqrt3_half + 0.08, f'Cand {labels[0]}', ha='center', 
                               fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='bottom')
            ax_tern_after.text(0.5, sqrt3_half + 0.08, f'Cand {labels[0]}', ha='center', 
                              fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='bottom')
            
            # Bottom labels: move further down and adjust horizontal spacing
            ax_tern_before.text(1.05, -0.12, f'Cand {labels[1]}', ha='center', 
                               fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            ax_tern_before.text(-0.05, -0.12, f'Cand {labels[2]}', ha='center', 
                               fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            
            ax_tern_after.text(1.05, -0.12, f'Cand {labels[1]}', ha='center', 
                              fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            ax_tern_after.text(-0.05, -0.12, f'Cand {labels[2]}', ha='center', 
                              fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            
            # Expand ternary plots vertically to use more of the available space
            # Get current positions
            bbox_before = ax_tern_before.get_position()
            bbox_after = ax_tern_after.get_position()
            
            # Expand vertically by increasing height and moving bottom edge down
            expansion_factor = 1.2  # Expand by 20%
            new_height = bbox_before.height * expansion_factor
            # Move bottom edge down to use more space, but leave room for legend
            new_y0 = max(0.05, bbox_before.y0 - (new_height - bbox_before.height) * 0.4)
            new_height = min(new_height, bbox_before.y1 - new_y0)  # Don't exceed top
            
            # Apply new positions
            ax_tern_before.set_position([bbox_before.x0, new_y0, bbox_before.width, new_height])
            ax_tern_after.set_position([bbox_after.x0, new_y0, bbox_after.width, new_height])
            
            # Update legend position based on new axes positions
            bbox_before = ax_tern_before.get_position()
            # Move legend left (reduce x) and up (increase y)
            legend_x = (bbox_before.x0 + bbox_after.x1) / 2 - 0.03  # Shift left (greater negative number means more left)
            legend_y = max(0.02, bbox_before.y0 - 0.06)  # Move up (greater negative number means lower)
            
            # Create legend below plots
            fig.legend(handles, labels_legend, 
                      loc='upper center',
                      bbox_to_anchor=(legend_x, legend_y),
                      fontsize=self.PLOT_LEGEND_FONTSIZE,
                      frameon=True,
                      ncol=4)
        else:
            ax_placeholder = fig.add_subplot(gs[1, 0])
            ax_placeholder.axis('off')
            ax_placeholder.text(0.5, 0.5, "Ternary plot requires m=3", ha='center', va='center', fontsize=self.PLOT_TITLE_FONTSIZE)

        # D. Proportions Plot (Bottom Right Quadrant)
        ax_proportions = fig.add_subplot(gs[1, 1])
        # Plot proportions using the trajectory from the heatmap (GT mechanism)
        # This ensures consistency with phase transition plot which also uses GT mechanism
        traj_heatmap = data["heatmap"].get("traj")
        if traj_heatmap is not None and strategies is not None and perms is not None:
            # Use trajectory directly (GT mechanism) instead of recomputing from strategies
            # traj_heatmap has shape [T, m] where T is number of time steps after burn-in
            # strategies should also have shape [n, T] to match
            # #region agent log
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                traj_shape = traj_heatmap.shape if traj_heatmap is not None else None
                strategies_shape = strategies.shape if strategies is not None else None
                traj_first = list(traj_heatmap[0]) if traj_heatmap is not None and len(traj_heatmap) > 0 else None
                traj_last = list(traj_heatmap[-1]) if traj_heatmap is not None and len(traj_heatmap) > 0 else None
                center = np.array([1 / m] * m)
                dist_first = float(np.linalg.norm(traj_heatmap[0] - center)) if traj_heatmap is not None and len(traj_heatmap) > 0 else None
                dist_last = float(np.linalg.norm(traj_heatmap[-1] - center)) if traj_heatmap is not None and len(traj_heatmap) > 0 else None
                dist_avg_first_50 = float(np.linalg.norm(np.mean(traj_heatmap[:50], axis=0) - center)) if traj_heatmap is not None and len(traj_heatmap) >= 50 else None
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"T","location":"plot_dashboard.py:248","message":"Using trajectory for proportions plot","data":{{"traj_shape":{traj_shape},"strategies_shape":{strategies_shape},"traj_first":{traj_first},"traj_last":{traj_last},"dist_first":{dist_first},"dist_last":{dist_last},"dist_avg_first_50":{dist_avg_first_50},"alpha":{data["heatmap"]["alpha"]}}}}}\n')
            # #endregion
            
            plot_proportions(
                strategies,
                m=m,
                all_rankings=perms,
                labels=labels,
                mechanism="pairwise_majority",  # Not used when p_history is provided
                ax=ax_proportions,
                title=f"(e) Probability Distribution Evolution $\\alpha={data['heatmap']['alpha']:.3f}$",
                p_history=traj_heatmap,  # Pass trajectory directly (GT mechanism)
            )
        elif strategies is not None and perms is not None:
            # Fallback: compute from strategies if trajectory not available
            # #region agent log
            with open('/Users/lucas/Code/gt-voting/.cursor/debug.log', 'a') as f:
                f.write(f'{{"sessionId":"debug-session","runId":"run1","hypothesisId":"U","location":"plot_dashboard.py:268","message":"Fallback: computing from strategies","data":{{"alpha":{data["heatmap"]["alpha"]}}}}}\n')
            # #endregion
            plot_proportions(
                strategies,
                m=m,
                all_rankings=perms,
                labels=labels,
                mechanism="pairwise_majority",
                ax=ax_proportions,
                title=f"(e) Probability Distribution Evolution $\\alpha={data['heatmap']['alpha']:.3f}$",
            )
        else:
            ax_proportions.axis('off')
            ax_proportions.text(0.5, 0.5, "No strategy data available", ha='center', va='center', fontsize=self.PLOT_TITLE_FONTSIZE)

        # Align the two right-side plots (voter strategies and probability distribution)
        # Both have T=300 time steps, so they should be horizontally aligned
        if strategies is not None and perms is not None:
            # Get the number of time steps (T)
            n_voters, T = strategies.shape
            
            # Ensure both plots have the same x-axis limits and ticks for horizontal alignment
            # Set x-axis limits to match (0 to T-1)
            ax_heat.set_xlim(-0.5, T - 0.5)
            ax_proportions.set_xlim(-0.5, T - 0.5)
            
            # Use the same tick positions for both plots
            # Calculate evenly spaced ticks (same logic as in plot_voter_strategies and plot_proportions)
            if T <= 10:
                x_ticks = list(range(T))
            else:
                n_ticks = min(8, max(6, T // 50))
                x_ticks = np.linspace(0, T - 1, n_ticks, dtype=int)
                if x_ticks[0] != 0:
                    x_ticks[0] = 0
                if x_ticks[-1] != T - 1:
                    x_ticks[-1] = T - 1
                x_ticks = list(dict.fromkeys(x_ticks))
            
            ax_heat.set_xticks(x_ticks)
            ax_proportions.set_xticks(x_ticks)
            
            # Apply tight_layout first to get initial positioning
            plt.tight_layout()
            
            # Now manually adjust positions to ensure same main plot width and aligned right margins
            # Get current positions after tight_layout
            bbox_heat = ax_heat.get_position()
            bbox_proportions = ax_proportions.get_position()
            
            # Find the colorbar from the voter strategies plot
            # The colorbar is created in plot_voter_strategies
            from matplotlib.colorbar import Colorbar
            cbar = None
            
            # Find colorbar by checking all Colorbar instances
            # The colorbar should be positioned to the right of ax_heat
            for child in fig.get_children():
                if isinstance(child, Colorbar):
                    try:
                        cbar_pos = child.ax.get_position()
                        # Check if colorbar is positioned to the right of ax_heat
                        # and has similar vertical position (within tolerance)
                        if (cbar_pos.x0 > bbox_heat.x1 - 0.01 and  # Slightly to the right of ax_heat
                            abs(cbar_pos.y0 - bbox_heat.y0) < 0.15 and  # Similar vertical position
                            abs(cbar_pos.height - bbox_heat.height) < 0.15):  # Similar height
                            cbar = child
                            break
                    except:
                        pass
            
            # Calculate target positions for main plot areas
            # Use the leftmost left edge and ensure both have the same width
            target_left = min(bbox_heat.x0, bbox_proportions.x0)
            
            # Position legends/colorbars at the right margin of the main figure
            # Use figure coordinates - position at right edge (1.0) to glue to margin
            # Calculate from right edge: colorbar width will determine left edge position
            figure_right_edge = 1.0
            cbar_width = 0.015  # Width of colorbar
            legend_start_x = figure_right_edge - cbar_width  # Position so right edge is at figure edge
            
            # Calculate main plot width - leave gap before legend to prevent overlap
            # Leave ~0.05 gap between main plot and legend
            target_right_main = legend_start_x - 0.05
            
            # Calculate new positions - both plots should have the same main plot area
            new_width = target_right_main - target_left
            
            # Set new positions for both axes (same width, aligned left edge)
            ax_heat.set_position([target_left, bbox_heat.y0, new_width, bbox_heat.height])
            ax_proportions.set_position([target_left, bbox_proportions.y0, new_width, bbox_proportions.height])
            
            # Adjust the legend position in proportions plot - keep original positioning
            # The "A, B, C" legend was already correctly positioned, don't change it
            legend = ax_proportions.get_legend()
            if legend is not None:
                # Remove the old legend
                legend.remove()
                # Create new legend with original positioning (was correct)
                handles, labels_legend = ax_proportions.get_legend_handles_labels()
                # Keep original positioning: bbox_to_anchor with loc='upper left'
                ax_proportions.legend(
                    handles, labels_legend,
                    bbox_to_anchor=(legend_start_x, 1.0),
                    loc='upper left',
                    framealpha=0.9,
                    fontsize=self.PLOT_LEGEND_FONTSIZE
                )
            
            # Now adjust the colorbar position to align with the legend at right margin
            # Do this AFTER setting axes positions to ensure it doesn't get auto-adjusted
            if cbar is not None:
                # Get the updated axes position after repositioning
                bbox_heat_updated = ax_heat.get_position()
                # Position colorbar so its right edge is at the figure's right edge (1.0)
                # This "glues" it to the right margin like the "A, B, C" legend
                # Set position in figure coordinates: [left, bottom, width, height]
                cbar.ax.set_position([legend_start_x, bbox_heat_updated.y0, cbar_width, bbox_heat_updated.height])
                
            # Final repositioning of colorbar to ensure it's glued to right margin
            # This is done at the very end to override any automatic adjustments
            if cbar is not None:
                bbox_heat_final = ax_heat.get_position()
                # Position colorbar so its right edge is at figure edge (1.0)
                cbar.ax.set_position([legend_start_x, bbox_heat_final.y0, cbar_width, bbox_heat_final.height])
        else:
            plt.tight_layout()
        
        # Apply manual subplot adjustments: left, bottom, right, top, wspace, hspace
        # These values were determined through interactive adjustment
        fig.subplots_adjust(left=0.07, bottom=0.073, right=0.932, top=0.918, wspace=0.24, hspace=0.195)
        
        # Final repositioning of colorbar AFTER subplots_adjust to ensure it's glued to right margin
        # This ensures the colorbar stays at the figure's right edge (1.0) even after layout adjustments
        if strategies is not None and perms is not None:
            from matplotlib.colorbar import Colorbar
            cbar = None
            # Find the colorbar again after subplots_adjust
            bbox_heat_final = ax_heat.get_position()
            for child in fig.get_children():
                if isinstance(child, Colorbar):
                    try:
                        cbar_pos = child.ax.get_position()
                        # Check if colorbar is positioned to the right of ax_heat
                        if (cbar_pos.x0 > bbox_heat_final.x1 - 0.01 and 
                            abs(cbar_pos.y0 - bbox_heat_final.y0) < 0.15 and
                            abs(cbar_pos.height - bbox_heat_final.height) < 0.15):
                            cbar = child
                            break
                    except:
                        pass
            
            if cbar is not None:
                # Position colorbar so its right edge is at figure edge (1.0)
                figure_right_edge = 1.0
                cbar_width = 0.015
                legend_start_x = figure_right_edge - cbar_width
                cbar.ax.set_position([legend_start_x, bbox_heat_final.y0, cbar_width, bbox_heat_final.height])
        
        return fig


# Backward compatibility wrapper
def plot_dashboard(*args, **kwargs):
    """Backward compatibility wrapper for plot_dashboard function."""
    plotter = DashboardPlot()
    return plotter.plot(*args, **kwargs)
