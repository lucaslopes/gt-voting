"""Dashboard plotting function for combined 2×2 grid view (4 quadrants)."""

import numpy as np
import matplotlib.pyplot as plt
from core.rankings_core import candidate_labels
from core.phase_transition import warp_alpha_axis
from plots.plot_voter_strategies import plot_voter_strategies
from plots.plot_ternary import plot_single_ternary
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

        def _fmt_trim(x, max_decimals=3):
            """Format with up to max_decimals, trimming trailing zeros (e.g. 0.500 -> 0.5)."""
            try:
                s = f"{float(x):.{max_decimals}f}"
            except (TypeError, ValueError):
                return str(x)
            return s.rstrip("0").rstrip(".")
        
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
                             label=f"Threshold α≈{_fmt_trim(threshold_alpha)}")
        
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
            ax_phase.set_xticklabels([_fmt_trim(a) for a in tick_alphas_original])
        
        # B. Strategy Heatmap (Top Right Quadrant)
        ax_heat = fig.add_subplot(gs[0, 1])
        plot_voter_strategies(
            strategies,
            perms,
            labels=labels,
            ax=ax_heat,
            title=rf"(d) Voter Strategy Evolution $\alpha={_fmt_trim(data['heatmap']['alpha'])}$",
            title_fontsize=self.PLOT_TITLE_FONTSIZE
        )
        
        # C. Ternary Trajectories (Before and After Threshold) - Bottom Left Quadrant
        if ternary is not None and ternary.get("traj_before") is not None and ternary.get("traj_after") is not None:
            traj_before = ternary["traj_before"]
            traj_after = ternary["traj_after"]
            
            # Get initial baseline outcome if available (for "Start" point)
            p_initial_baseline = ternary.get("p_initial_baseline")

            # Ternary legend placement: single source of truth.
            # dx < 0 moves left; dy > 0 moves up (figure coordinates).
            ternary_legend_dx = -0.085
            ternary_legend_dy = 0.12

            # Gap between the two ternary plots (figure coordinates).
            # Increasing this will reduce each plot's width to keep them inside the bottom-left quadrant,
            # but the two triangles will remain identically scaled (widths allocated proportional to x-range).
            ternary_gap = 0.05

            # Ternary top label/title spacing: single source of truth.
            # Increase these together to move both upward proportionally.
            ternary_top_label_dy = 0.00  # y offset above the top vertex (data coords)
            ternary_title_pad = 22     # title padding (points)

            def _ternary_legend_anchor(ax_left, ax_right, dx, dy):
                """Compute figure-coordinate anchor for the shared ternary legend."""
                bbox_left = ax_left.get_position()
                bbox_right = ax_right.get_position()
                x = (bbox_left.x1 + bbox_right.x0) / 2 + dx
                y = (bbox_left.y0 + bbox_left.y1) / 2 + dy
                return x, y
            
            # Create nested grid for two ternary plots in bottom-left quadrant
            # Use more vertical space by adjusting hspace and reducing bottom padding
            gs_ternary = gs[1, 0].subgridspec(1, 2, hspace=0.2, wspace=0.2)
            
            # Plot Before Threshold using reusable function
            ax_tern_before = fig.add_subplot(gs_ternary[0, 0])
            handles_before, labels_legend = plot_single_ternary(
                ax_tern_before,
                traj_before,
                p_initial_baseline=p_initial_baseline,
                labels=labels,
                title=f"(b) Before Threshold\n$\\alpha={_fmt_trim(alpha_before)}$",
                show_instantaneous=True,
                show_running_avg=True,
                show_start=True,
                show_end=True,
                instant_alpha=0.3,
                instant_lw=0.5,
                avg_lw=2,
                use_gradient=True,  # Use gradient color from start to finish
                show_labels=False,  # Dashboard handles label positioning manually
                title_fontsize=self.PLOT_TITLE_FONTSIZE,  # Use dashboard font size
                label_fontsize=self.PLOT_AXIS_LABEL_FONTSIZE,  # Use dashboard font size
            )
            
            # Plot After Threshold using reusable function
            ax_tern_after = fig.add_subplot(gs_ternary[0, 1])
            handles_after, _ = plot_single_ternary(
                ax_tern_after,
                traj_after,
                p_initial_baseline=p_initial_baseline,
                labels=labels,
                title=f"(c) After Threshold\n$\\alpha={_fmt_trim(alpha_after)}$",
                show_instantaneous=True,
                show_running_avg=True,
                show_start=True,
                show_end=True,
                instant_alpha=0.3,
                instant_lw=0.5,
                avg_lw=2,
                use_gradient=True,  # Use gradient color from start to finish
                show_labels=False,  # Dashboard handles label positioning manually
                title_fontsize=self.PLOT_TITLE_FONTSIZE,  # Use dashboard font size
                label_fontsize=self.PLOT_AXIS_LABEL_FONTSIZE,  # Use dashboard font size
            )
            
            # Get legend handles and labels (they're the same for both plots)
            handles = handles_before
            
            # Set explicit axes limits to tightly bound the triangles and use more vertical space
            # Triangle is scaled by 2.0 in plot_single_ternary, so adjust limits accordingly
            sqrt3_half = np.sqrt(3) / 2
            scale_factor = 2.0  # Match the scale factor used in plot_single_ternary
            center_x = 0.5
            center_y = np.sqrt(3) / 6
            # Calculate triangle bounds after scaling
            tri_x_min = (0 - center_x) * scale_factor + center_x  # = -0.5
            tri_x_max = (1 - center_x) * scale_factor + center_x  # = 1.5
            tri_y_min = (0 - center_y) * scale_factor + center_y  # ≈ -0.289
            tri_y_max = (sqrt3_half - center_y) * scale_factor + center_y  # ≈ 1.443
            # Calculate padding to accommodate labels (reduced to minimize blank space)
            x_pad = 0.08  # Reduced padding
            # Keep identical axes limits so the triangles render at identical scale.
            # Horizontal "gluing" is handled later via set_position(...), not via asymmetric x-limits.
            x_pad_left = 0.1
            # Provide enough headroom for the top label + title.
            y_pad_top = 0.10 + ternary_top_label_dy
            y_pad_bottom = 0.08  # Reduced padding for bottom labels
            
            # Use identical x/y limits for both ternary plots (visual parity).
            ax_tern_before.set_xlim(tri_x_min - x_pad_left, tri_x_max + x_pad)
            ax_tern_before.set_ylim(tri_y_min - y_pad_bottom, tri_y_max + y_pad_top)
            
            ax_tern_after.set_xlim(tri_x_min - x_pad, tri_x_max + x_pad)
            ax_tern_after.set_ylim(tri_y_min - y_pad_bottom, tri_y_max + y_pad_top)
            
            # Reposition labels to avoid overlap
            # Put the top candidate label further above the triangle to avoid collision with title
            ax_tern_before.text(center_x, tri_y_max + ternary_top_label_dy, f'{labels[0]}', ha='center',
                               fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='bottom')
            ax_tern_after.text(center_x, tri_y_max + ternary_top_label_dy, f'{labels[0]}', ha='center',
                              fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='bottom')

            # Re-apply title with explicit padding (plot_single_ternary sets a title without pad).
            ax_tern_before.set_title(
                f"(b) Before Threshold\n$\\alpha={_fmt_trim(alpha_before)}$",
                fontsize=self.PLOT_TITLE_FONTSIZE,
                fontweight="bold",
                pad=ternary_title_pad,
            )
            ax_tern_after.set_title(
                f"(c) After Threshold\n$\\alpha={_fmt_trim(alpha_after)}$",
                fontsize=self.PLOT_TITLE_FONTSIZE,
                fontweight="bold",
                pad=ternary_title_pad,
            )
            
            # Bottom labels: position relative to scaled triangle bottom vertices
            ax_tern_before.text(tri_x_max + 0.05, tri_y_min - 0.12, f'{labels[1]}', ha='center', 
                               fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            ax_tern_before.text(tri_x_min - 0.05, tri_y_min - 0.12, f'{labels[2]}', ha='center', 
                               fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            
            ax_tern_after.text(tri_x_max + 0.05, tri_y_min - 0.12, f'{labels[1]}', ha='center', 
                              fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            ax_tern_after.text(tri_x_min - 0.05, tri_y_min - 0.12, f'{labels[2]}', ha='center', 
                              fontsize=self.PLOT_AXIS_LABEL_FONTSIZE, va='top')
            
            # Expand ternary plots vertically to use more of the available space
            # Get current positions
            bbox_before = ax_tern_before.get_position()
            bbox_after = ax_tern_after.get_position()
            
            # Expand vertically by increasing height and moving bottom edge down
            expansion_factor = 2.0  # Strong vertical expansion to fill canvas
            new_height = bbox_before.height * expansion_factor
            # Move bottom edge down aggressively so ternary plots sit close to bottom margin
            # Keep a very small padding (0.02) so labels don't get clipped
            new_y0 = max(0.02, bbox_before.y0 - (new_height - bbox_before.height) * 0.9)
            new_height = min(new_height, bbox_before.y1 - new_y0)  # Don't exceed top
            
            # Store original widths to preserve them
            tern_before_width = bbox_before.width
            tern_after_width = bbox_after.width
            
            # Apply new vertical positions (horizontal will be adjusted later after subplots_adjust)
            ax_tern_before.set_position([bbox_before.x0, new_y0, tern_before_width, new_height])
            ax_tern_after.set_position([bbox_after.x0, new_y0, tern_after_width, new_height])
            
            # Update legend position based on new axes positions
            bbox_before = ax_tern_before.get_position()
            bbox_after = ax_tern_after.get_position()
            legend_x, legend_y = _ternary_legend_anchor(
                ax_tern_before, ax_tern_after, ternary_legend_dx, ternary_legend_dy
            )
            
            # Create legend between plots (1 column, 4 rows)
            ternary_legend = fig.legend(handles, labels_legend,
                      loc='center left',
                      bbox_to_anchor=(legend_x, legend_y),
                      fontsize=self.PLOT_LEGEND_FONTSIZE,
                      frameon=True,
                      ncol=1)
        else:
            ax_placeholder = fig.add_subplot(gs[1, 0])
            ax_placeholder.axis('off')
            ax_placeholder.text(0.5, 0.5, "Ternary plot requires m=3", ha='center', va='center', fontsize=self.PLOT_TITLE_FONTSIZE)

        # D. Proportions Plot (Bottom Right Quadrant)
        ax_proportions = fig.add_subplot(gs[1, 1])
        # Plot proportions using the trajectory from the heatmap (GT mechanism)
        # This ensures consistency with phase transition plot which also uses GT mechanism
        traj_heatmap = data["heatmap"].get("traj")
        # Subplot (e) title horizontal alignment (x in axes coords: 0=left, 0.5=center, 1=right)
        e_title_x = 0.53
        if traj_heatmap is not None and strategies is not None and perms is not None:
            # Use trajectory directly (GT mechanism) instead of recomputing from strategies
            # traj_heatmap has shape [T, m] where T is number of time steps after burn-in
            # strategies should also have shape [n, T] to match
            e_title = f"(e) Probability Distribution Evolution $\\alpha={_fmt_trim(data['heatmap']['alpha'])}$"
            plot_proportions(
                strategies,
                m=m,
                all_rankings=perms,
                labels=labels,
                mechanism="pairwise_majority",  # Not used when p_history is provided
                ax=ax_proportions,
                title=e_title,
                p_history=traj_heatmap,  # Pass trajectory directly (GT mechanism)
            )
            ax_proportions.set_title(
                e_title,
                fontsize=self.PLOT_TITLE_FONTSIZE,
                fontweight="bold",
                pad=self.PLOT_TITLE_PAD,
                x=e_title_x,
            )
        elif strategies is not None and perms is not None:
            # Fallback: compute from strategies if trajectory not available
            e_title = f"(e) Probability Distribution Evolution $\\alpha={_fmt_trim(data['heatmap']['alpha'])}$"
            plot_proportions(
                strategies,
                m=m,
                all_rankings=perms,
                labels=labels,
                mechanism="pairwise_majority",
                ax=ax_proportions,
                title=e_title,
            )
            ax_proportions.set_title(
                e_title,
                fontsize=self.PLOT_TITLE_FONTSIZE,
                fontweight="bold",
                pad=self.PLOT_TITLE_PAD,
                x=e_title_x,
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
            # Calculate from right edge: use maximum of colorbar and legend widths
            figure_right_edge = 1.0
            cbar_width = 0.015  # Width of colorbar
            
            # Get proportions legend width if it exists (before it gets removed/repositioned)
            proportions_legend = ax_proportions.get_legend()
            legend_width = 0.0
            if proportions_legend is not None:
                try:
                    # Get legend width in figure coordinates
                    legend_bbox = proportions_legend.get_window_extent()
                    legend_bbox_fig = legend_bbox.transformed(fig.transFigure.inverted())
                    legend_width = legend_bbox_fig.width
                except:
                    # Fallback: estimate legend width (typically ~0.03-0.04 for 3 candidates)
                    legend_width = 0.035
            
            # Use the maximum width to ensure both colorbar and legend fit
            # Add some safety margin
            max_sidebar_width = max(cbar_width, legend_width, 0.02) + 0.01  # Extra 0.01 for safety
            legend_start_x = figure_right_edge - max_sidebar_width  # Position so right edge is at figure edge
            
            # Calculate main plot width - leave gap before legend/colorbar to prevent overlap
            # Leave larger gap (0.08) between main plot and legend to prevent overlap
            target_right_main = legend_start_x - 0.08
            
            # Calculate new positions - both plots should have the same main plot area width
            new_width = target_right_main - target_left
            
            # Ensure width is positive
            if new_width <= 0:
                new_width = min(bbox_heat.width, bbox_proportions.width)
            
            # Set new positions for both axes (same width, aligned left edge)
            ax_heat.set_position([target_left, bbox_heat.y0, new_width, bbox_heat.height])
            ax_proportions.set_position([target_left, bbox_proportions.y0, new_width, bbox_proportions.height])
            
            # Verify both plots now have the same width
            bbox_heat_after = ax_heat.get_position()
            bbox_proportions_after = ax_proportions.get_position()
            # Force same width if they differ (shouldn't happen, but safety check)
            if abs(bbox_heat_after.width - bbox_proportions_after.width) > 0.001:
                final_width = min(bbox_heat_after.width, bbox_proportions_after.width)
                ax_heat.set_position([target_left, bbox_heat_after.y0, final_width, bbox_heat_after.height])
                ax_proportions.set_position([target_left, bbox_proportions_after.y0, final_width, bbox_proportions_after.height])
            
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
        # Move right column closer to right margin and increase gap between columns
        fig.subplots_adjust(left=0.07, bottom=0.073, right=0.97, top=0.918, wspace=0.5, hspace=0.195)

        # After the final layout pass, force the ternary axes to sit very close to the bottom margin
        # and maximize horizontal separation (left plot glued to left margin, right plot glued to right edge of subplot).
        # (subplots_adjust can move them back up, so we do this at the end.)
        if ternary is not None and 'ax_tern_before' in locals() and 'ax_tern_after' in locals():
            bbox_before_final = ax_tern_before.get_position()
            bbox_after_final = ax_tern_after.get_position()

            target_y0 = 0.02  # "almost glued" to the bottom of the main figure (only ternary axes)
            # Preserve the current top edge; just slide the bottom down to target_y0.
            new_height_final = max(0.01, max(bbox_before_final.y1, bbox_after_final.y1) - target_y0)

            # Horizontal repositioning: maximize separation within the bottom-left subplot region
            # User-tunable spacing between the two ternary axes (figure coordinates).
            ternary_horizontal_spacing = max(0.0, float(ternary_gap))
            
            # Get the bounds of the bottom-left subplot region (gs[1, 0])
            # After subplots_adjust, get the actual position from the gridspec
            gs_bottom_left_bbox = gs[1, 0].get_position(fig)
            subplot_right_edge = gs_bottom_left_bbox.x1
            
            # Left margin of main figure - use a very small value to glue left plot to screen edge
            figure_left_margin = 0.02  # Almost glued to left edge of screen
            
            # Allocate widths proportional to x-range so both triangles render at the same scale
            # under equal-aspect axes (scale ∝ axes_width / data_xrange).
            xlim_before = ax_tern_before.get_xlim()
            xlim_after = ax_tern_after.get_xlim()
            xrange_before = float(xlim_before[1] - xlim_before[0])
            xrange_after = float(xlim_after[1] - xlim_after[0])
            denom = max(1e-12, xrange_before + xrange_after)

            total_span = subplot_right_edge - figure_left_margin
            total_width = max(0.01, total_span - ternary_horizontal_spacing)
            tern_before_width = total_width * (xrange_before / denom)
            tern_after_width = max(0.01, total_width - tern_before_width)

            tern_before_x0 = figure_left_margin
            tern_after_x0 = tern_before_x0 + tern_before_width + ternary_horizontal_spacing
            
            # Apply new positions (vertical and horizontal)
            ax_tern_before.set_position([tern_before_x0, target_y0, tern_before_width, new_height_final])
            ax_tern_after.set_position([tern_after_x0, target_y0, tern_after_width, new_height_final])

            # Re-center the ternary legend after shifting the axes
            if 'ternary_legend' in locals() and ternary_legend is not None:
                legend_x_final, legend_y_final = _ternary_legend_anchor(
                    ax_tern_before, ax_tern_after, ternary_legend_dx, ternary_legend_dy
                )
                ternary_legend.set_bbox_to_anchor(
                    (legend_x_final, legend_y_final), transform=fig.transFigure
                )
        
        # Shift right column subplots further right to minimize blank space on the right
        # Get current positions of right column subplots
        bbox_heat_current = ax_heat.get_position()
        bbox_proportions_current = ax_proportions.get_position()
        
        # Calculate optimal right edge position accounting for colorbar/legend
        # Estimate space needed: colorbar (~0.015) + legend (~0.04) + gap (~0.01) = ~0.065
        figure_right_edge = 1.0
        sidebar_width_estimate = 0.065  # Space for colorbar + legend + gap
        target_right_edge = figure_right_edge - sidebar_width_estimate
        
        # Calculate shift needed for both plots
        # Use the rightmost plot's right edge as reference
        current_rightmost = max(bbox_heat_current.x1, bbox_proportions_current.x1)
        shift_right = target_right_edge - current_rightmost
        
        # Only shift if there's significant space to the right (more than 0.02)
        if shift_right > 0.02:
            # Shift both right column subplots while maintaining their width
            ax_heat.set_position([
                bbox_heat_current.x0 + shift_right,
                bbox_heat_current.y0,
                bbox_heat_current.width,
                bbox_heat_current.height
            ])
            ax_proportions.set_position([
                bbox_proportions_current.x0 + shift_right,
                bbox_proportions_current.y0,
                bbox_proportions_current.width,
                bbox_proportions_current.height
            ])
        
        # Final repositioning of colorbar AFTER subplots_adjust to ensure it's glued to right margin
        # This ensures the colorbar stays at the figure's right edge (1.0) even after layout adjustments
        # Also ensure both right-side plots still have the same width after subplots_adjust
        if strategies is not None and perms is not None:
            # Re-check and align widths after subplots_adjust (which may have changed positions)
            bbox_heat_final = ax_heat.get_position()
            bbox_proportions_final = ax_proportions.get_position()
            
            # If widths differ, make them the same (use the smaller width to be safe)
            if abs(bbox_heat_final.width - bbox_proportions_final.width) > 0.001:
                target_left_final = min(bbox_heat_final.x0, bbox_proportions_final.x0)
                final_width = min(bbox_heat_final.width, bbox_proportions_final.width)
                ax_heat.set_position([target_left_final, bbox_heat_final.y0, final_width, bbox_heat_final.height])
                ax_proportions.set_position([target_left_final, bbox_proportions_final.y0, final_width, bbox_proportions_final.height])
                # Update bbox references after repositioning
                bbox_heat_final = ax_heat.get_position()
                bbox_proportions_final = ax_proportions.get_position()
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
                # Use same calculation as earlier to maintain consistency
                figure_right_edge = 1.0
                cbar_width = 0.015
                # Get proportions legend width for consistency
                proportions_legend_final = ax_proportions.get_legend()
                legend_width_final = 0.0
                if proportions_legend_final is not None:
                    try:
                        legend_bbox_final = proportions_legend_final.get_window_extent()
                        legend_bbox_fig_final = legend_bbox_final.transformed(fig.transFigure.inverted())
                        legend_width_final = legend_bbox_fig_final.width
                    except:
                        legend_width_final = 0.035
                max_sidebar_width_final = max(cbar_width, legend_width_final, 0.02) + 0.01
                legend_start_x_final = figure_right_edge - max_sidebar_width_final
                cbar.ax.set_position([legend_start_x_final, bbox_heat_final.y0, cbar_width, bbox_heat_final.height])
                
                # Do not modify the proportions legend here; it is fully managed
                # inside plot_proportions (including order and colors). We only
                # reposition the colorbar at this stage.
        
        return fig


# Backward compatibility wrapper
def plot_dashboard(*args, **kwargs):
    """Backward compatibility wrapper for plot_dashboard function."""
    plotter = DashboardPlot()
    return plotter.plot(*args, **kwargs)
