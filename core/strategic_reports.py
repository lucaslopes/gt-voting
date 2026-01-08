"""Core functionality for generating strategic reports that evolve over time."""

import numpy as np
from core.rankings_core import generate_rankings
from core.utils import spawn_rng


def spearman_footrule_distance(ranking1, ranking2):
    """
    Calculate Spearman footrule distance between two rankings.
    
    The Spearman footrule distance is the sum of absolute differences in positions
    for each candidate between the two rankings.
    
    Args:
        ranking1: First ranking tuple (e.g., (0, 1, 2))
        ranking2: Second ranking tuple (e.g., (1, 0, 2))
    
    Returns:
        Integer distance (sum of absolute position differences)
    
    Example:
        >>> spearman_footrule_distance((0, 1, 2), (1, 0, 2))
        2
        # Candidate 0: |0-1| = 1
        # Candidate 1: |1-0| = 1
        # Candidate 2: |2-2| = 0
        # Total: 2
    """
    if len(ranking1) != len(ranking2):
        raise ValueError(f"Rankings must have same length: {len(ranking1)} vs {len(ranking2)}")
    
    # Create position maps: candidate -> position
    pos1 = {candidate: pos for pos, candidate in enumerate(ranking1)}
    pos2 = {candidate: pos for pos, candidate in enumerate(ranking2)}
    
    # Calculate sum of absolute position differences
    distance = sum(abs(pos1[c] - pos2[c]) for c in pos1)
    return distance


# Distance metric registry
DISTANCE_METRICS = {
    "spearman": spearman_footrule_distance,
    # Future additions can be added here:
    # "kendall_tau": kendall_tau_distance,
    # "levenshtein": levenshtein_distance,
}


def get_distance_function(metric_name="spearman"):
    """
    Get distance function by name from registry.
    
    Args:
        metric_name: Name of the distance metric (default: "spearman")
    
    Returns:
        Distance function that takes two rankings and returns an integer distance
    
    Raises:
        ValueError: If metric_name is not in the registry
    """
    if metric_name not in DISTANCE_METRICS:
        available = list(DISTANCE_METRICS.keys())
        raise ValueError(f"Unknown distance metric: {metric_name}. "
                        f"Available: {available}")
    return DISTANCE_METRICS[metric_name]


def get_max_distance(m, metric_name="spearman"):
    """
    Calculate maximum possible distance for m candidates with given metric.
    
    Args:
        m: Number of candidates
        metric_name: Name of the distance metric (default: "spearman")
    
    Returns:
        Integer maximum distance
    
    Raises:
        ValueError: If metric_name is not supported
    """
    if metric_name == "spearman":
        # Maximum Spearman footrule distance occurs when rankings are completely reversed
        # For m candidates, max distance = m*(m-1) when all positions are swapped
        # Actually, for complete reversal: positions go from 0..(m-1) to (m-1)..0
        # Sum of differences: sum(|i - (m-1-i)|) for i in range(m)
        # = sum(|2i - (m-1)|) for i in range(m)
        # For even m: = 2 * sum(i) for i in range(m/2) = 2 * (m/2 * (m/2-1) / 2) = m*(m-1)/2
        # For odd m: similar calculation
        # Actually simpler: max occurs when completely reversed
        # Position i in first maps to position (m-1-i) in second
        # Distance = sum(|i - (m-1-i)|) = sum(|2i - (m-1)|)
        # This simplifies to: if m is even, m^2/2; if odd, (m^2-1)/2
        # But let's use the simpler formula: m*(m-1) for the theoretical maximum
        # Actually, let's calculate it properly:
        # For complete reversal: ranking1 = (0,1,2,...,m-1), ranking2 = (m-1,m-2,...,0)
        # Distance = sum(|i - (m-1-i)|) for i in range(m)
        # = sum(|2i - (m-1)|) for i in range(m)
        # For m=3: |0-2| + |1-1| + |2-0| = 2 + 0 + 2 = 4
        # For m=4: |0-3| + |1-2| + |2-1| + |3-0| = 3 + 1 + 1 + 3 = 8
        # Pattern: m*(m-1) when m is even? Let's check m=3: 3*2=6, but we got 4
        # Actually: sum(|2i - (m-1)|) for i in range(m)
        # For m=3: |0-2| + |2-2| + |4-2| = 2 + 0 + 2 = 4
        # For m=4: |0-3| + |2-3| + |4-3| + |6-3| = 3 + 1 + 1 + 3 = 8
        # Pattern: m^2/2 if m even, (m^2-1)/2 if m odd
        # For m=3: (9-1)/2 = 4 ✓
        # For m=4: 16/2 = 8 ✓
        if m % 2 == 0:
            return m * m // 2
        else:
            return (m * m - 1) // 2
    elif metric_name == "kendall_tau":
        # Maximum Kendall Tau distance is the maximum number of inversions
        # For m candidates, max inversions = m*(m-1)/2
        return m * (m - 1) // 2
    else:
        raise ValueError(f"Max distance calculation not implemented for metric: {metric_name}")


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
