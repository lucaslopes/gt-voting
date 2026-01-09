"""Similarity-based strategy for evolving voter reports."""

import numpy as np
from strategies.BaseStrategy import BaseStrategy
from core.distance_metrics import get_distance_function, get_max_distance
from core.utils import spawn_rng


class SimilarityStrategy(BaseStrategy):
    """
    Similarity-based strategy for evolving voter reports.
    
    Reports start from honest_reports and evolve based on the anchor_strength parameter.
    The anchor_strength parameter (0-1) controls how closely reports stay to their original
    honest reports, with anchor_strength=1 meaning no change and anchor_strength=0 allowing
    completely random changes. Similarity is measured using distance metrics.
    """
    
    def __init__(self, distance_metric="spearman"):
        """
        Initialize SimilarityStrategy with a distance metric.
        
        Args:
            distance_metric: Either a string name (e.g., "spearman", "kendall_tau")
                           or a callable function that takes two rankings and returns distance.
                           If string, must be in the distance metrics registry.
        """
        self.distance_metric = distance_metric
        
        # If it's a string, get the function from registry
        if isinstance(distance_metric, str):
            self.distance_func = get_distance_function(distance_metric)
            self.metric_name = distance_metric
        elif callable(distance_metric):
            # If it's a callable, use it directly
            self.distance_func = distance_metric
            self.metric_name = "custom"
        else:
            raise ValueError(f"distance_metric must be a string or callable, got {type(distance_metric)}")
    
    def generate_reports(self, honest_reports, T, m, seed=None, rng=None, anchor_strength=0.5):
        """
        Generate strategic reports that evolve over T iterations.
        
        Reports start from honest_reports and evolve based on the anchor_strength parameter.
        The anchor_strength parameter (0-1) controls how closely reports stay to their original
        honest reports, with anchor_strength=1 meaning no change and anchor_strength=0 allowing
        completely random changes.
        
        Args:
            honest_reports: List of ranking tuples (baseline honest reports), one per voter
            T: Number of iterations (time steps)
            m: Number of candidates
            seed: Random seed for reproducibility (used if rng is None)
            rng: Optional numpy Generator (if provided, uses this instead of creating new one)
            anchor_strength: Float in [0, 1] controlling how much reports stay close to honest reports
                   1.0 = reports never change (stay at honest reports)
                   0.0 = reports can change completely randomly
        
        Returns:
            numpy array of shape [n, T+1] where:
            - n is the number of voters
            - Column 0 contains honest reports (initial state)
            - Columns 1..T contain evolved reports at each iteration
            - Each cell contains a ranking index (position in all_rankings)
        
        Raises:
            ValueError: If honest_reports is empty, T < 1, m < 1, anchor_strength not in [0,1], or other validation fails
        """
        # Validate parameters
        self.validate_parameters(T, m, anchor_strength=anchor_strength)
        n, candidates = self.validate_honest_reports(honest_reports, m)
        
        if not (0 <= anchor_strength <= 1):
            raise ValueError("anchor_strength must be between 0 and 1")
        
        # Get all possible rankings
        all_rankings = self.get_all_rankings(m, alphabetical=False)
        n_rankings = len(all_rankings)
        
        # Create mapping from ranking tuple to index
        ranking_to_index = {ranking: idx for idx, ranking in enumerate(all_rankings)}
        
        # Calculate maximum possible distance for this metric
        # If using custom function, we can't calculate max distance, so use a heuristic
        if self.metric_name == "custom":
            # For custom functions, estimate max distance as m*(m-1) (conservative estimate)
            max_possible_distance = m * (m - 1)
        else:
            max_possible_distance = get_max_distance(m, self.metric_name)
        
        # Initialize RNG
        rng = spawn_rng(seed, rng)
        
        # Initialize reports array: [n, T+1]
        # Column 0 will be honest reports, columns 1..T will be evolved reports
        reports = np.zeros((n, T + 1), dtype=int)
        
        # Convert honest reports to indices and store in column 0
        for i, ranking in enumerate(honest_reports):
            reports[i, 0] = ranking_to_index[ranking]
        
        # Evolve reports over T iterations
        for t in range(1, T + 1):
            for i in range(n):
                # With probability = anchor_strength: keep same report (copy from t-1)
                # With probability = 1 - anchor_strength: change report
                if rng.random() < anchor_strength:
                    # Keep same report
                    reports[i, t] = reports[i, t - 1]
                else:
                    # Change report
                    current_ranking_idx = reports[i, t - 1]
                    current_ranking = all_rankings[current_ranking_idx]
                    
                    # Calculate max_distance based on anchor_strength
                    # anchor_strength=1: max_distance=0 (only identical rankings)
                    # anchor_strength=0: max_distance=infinity (all rankings)
                    # For intermediate values: max_distance = (1 - anchor_strength) * max_possible_distance
                    if anchor_strength >= 1.0:
                        max_distance = 0
                    elif anchor_strength <= 0.0:
                        max_distance = float('inf')
                    else:
                        max_distance = (1 - anchor_strength) * max_possible_distance
                    
                    # Find similar rankings within max_distance
                    similar_indices = self._find_similar_rankings(
                        current_ranking,
                        all_rankings,
                        max_distance
                    )
                    
                    # If no similar rankings found (shouldn't happen, but handle edge case)
                    if not similar_indices:
                        # Fall back to current ranking
                        reports[i, t] = current_ranking_idx
                    else:
                        # Randomly sample one from similar rankings
                        reports[i, t] = rng.choice(similar_indices)
        
        return reports
    
    def _find_similar_rankings(self, current_ranking, all_rankings, max_distance):
        """
        Find rankings within max_distance of current_ranking.
        
        Args:
            current_ranking: The ranking to compare against (tuple)
            all_rankings: List of all possible rankings (list of tuples)
            max_distance: Maximum allowed distance (integer, or float('inf'))
        
        Returns:
            List of ranking indices (positions in all_rankings) that are within max_distance
        """
        similar_indices = []
        
        for idx, ranking in enumerate(all_rankings):
            distance = self.distance_func(current_ranking, ranking)
            if distance <= max_distance:
                similar_indices.append(idx)
        
        return similar_indices
