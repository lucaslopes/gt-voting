"""Core functionality for generating strategic reports that evolve over time."""

import numpy as np
from core.rankings_core import generate_rankings
from core.utils import spawn_rng
from core.distance_metrics import get_distance_function, get_max_distance


def find_similar_rankings(current_ranking, all_rankings, max_distance, distance_func):
    """
    Find rankings within max_distance of current_ranking.
    
    Args:
        current_ranking: The ranking to compare against (tuple)
        all_rankings: List of all possible rankings (list of tuples)
        max_distance: Maximum allowed distance (integer, or float('inf'))
        distance_func: Distance function that takes two rankings and returns distance
    
    Returns:
        List of ranking indices (positions in all_rankings) that are within max_distance
    """
    similar_indices = []
    
    for idx, ranking in enumerate(all_rankings):
        distance = distance_func(current_ranking, ranking)
        if distance <= max_distance:
            similar_indices.append(idx)
    
    return similar_indices


def generate_strategic_reports(honest_reports, T, anchor, m, seed=None, rng=None, distance_metric="spearman"):
    """
    Generate strategic reports that evolve over T iterations.
    
    Reports start from honest_reports and evolve based on the anchor parameter.
    The anchor parameter (0-1) controls how closely reports stay to their original
    honest reports, with anchor=1 meaning no change and anchor=0 allowing
    completely random changes.
    
    Args:
        honest_reports: List of ranking tuples (baseline honest reports), one per voter
        T: Number of iterations (time steps)
        anchor: Float in [0, 1] controlling how much reports stay close to honest reports
                1.0 = reports never change (stay at honest reports)
                0.0 = reports can change completely randomly
        m: Number of candidates
        seed: Random seed for reproducibility (used if rng is None)
        rng: Optional numpy Generator (if None, creates new one from seed)
        distance_metric: Name of distance metric to use (default: "spearman")
    
    Returns:
        numpy array of shape [n, T+1] where:
        - n is the number of voters
        - Column 0 contains honest reports (initial state)
        - Columns 1..T contain evolved reports at each iteration
        - Each cell contains a ranking index (position in all_rankings)
    """
    # Get distance function
    distance_func = get_distance_function(distance_metric)
    
    # Get all possible rankings
    all_rankings = generate_rankings(m, alphabetical=False)
    n_rankings = len(all_rankings)
    
    # Create mapping from ranking tuple to index
    ranking_to_index = {ranking: idx for idx, ranking in enumerate(all_rankings)}
    
    # Calculate maximum possible distance for this metric
    max_possible_distance = get_max_distance(m, distance_metric)
    
    # Initialize RNG
    rng = spawn_rng(seed, rng)
    
    # Number of voters
    n = len(honest_reports)
    
    # Initialize reports array: [n, T+1]
    # Column 0 will be honest reports, columns 1..T will be evolved reports
    reports = np.zeros((n, T + 1), dtype=int)
    
    # Convert honest reports to indices and store in column 0
    for i, ranking in enumerate(honest_reports):
        reports[i, 0] = ranking_to_index[ranking]
    
    # Evolve reports over T iterations
    for t in range(1, T + 1):
        for i in range(n):
            # With probability = anchor: keep same report (copy from t-1)
            # With probability = 1 - anchor: change report
            if rng.random() < anchor:
                # Keep same report
                reports[i, t] = reports[i, t - 1]
            else:
                # Change report
                current_ranking_idx = reports[i, t - 1]
                current_ranking = all_rankings[current_ranking_idx]
                
                # Calculate max_distance based on anchor
                # anchor=1: max_distance=0 (only identical rankings)
                # anchor=0: max_distance=infinity (all rankings)
                # For intermediate values: max_distance = (1 - anchor) * max_possible_distance
                if anchor >= 1.0:
                    max_distance = 0
                elif anchor <= 0.0:
                    max_distance = float('inf')
                else:
                    max_distance = (1 - anchor) * max_possible_distance
                
                # Find similar rankings within max_distance
                similar_indices = find_similar_rankings(
                    current_ranking,
                    all_rankings,
                    max_distance,
                    distance_func
                )
                
                # If no similar rankings found (shouldn't happen, but handle edge case)
                if not similar_indices:
                    # Fall back to current ranking
                    reports[i, t] = current_ranking_idx
                else:
                    # Randomly sample one from similar rankings
                    reports[i, t] = rng.choice(similar_indices)
    
    return reports
