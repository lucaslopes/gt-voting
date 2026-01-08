"""Distance metrics for comparing rankings."""


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


def kendall_tau_distance(ranking1, ranking2):
    """
    Calculate Kendall Tau distance between two rankings.
    
    The Kendall Tau distance measures the number of pairwise disagreements (inversions)
    between two rankings. It counts the number of pairs of elements that are in
    different order in the two rankings.
    
    Args:
        ranking1: First ranking tuple (e.g., (0, 1, 2))
        ranking2: Second ranking tuple (e.g., (1, 0, 2))
    
    Returns:
        Integer distance (number of inversions)
    
    Example:
        >>> kendall_tau_distance((0, 1, 2), (1, 0, 2))
        1
        # One inversion: (0, 1) is ordered differently
    """
    if len(ranking1) != len(ranking2):
        raise ValueError(f"Rankings must have same length: {len(ranking1)} vs {len(ranking2)}")
    
    # Create position maps: candidate -> position in each ranking
    pos1 = {candidate: pos for pos, candidate in enumerate(ranking1)}
    pos2 = {candidate: pos for pos, candidate in enumerate(ranking2)}
    
    # Count inversions: pairs (i, j) where i < j in ranking1 but i > j in ranking2
    # (or vice versa - order differs between the two rankings)
    inversions = 0
    candidates = list(pos1.keys())
    
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            c1, c2 = candidates[i], candidates[j]
            # Check if order differs between the two rankings
            # In ranking1: c1 is at pos1[c1], c2 is at pos1[c2]
            # In ranking2: c1 is at pos2[c1], c2 is at pos2[c2]
            # If (pos1[c1] < pos1[c2] and pos2[c1] > pos2[c2]) or
            #    (pos1[c1] > pos1[c2] and pos2[c1] < pos2[c2]),
            # then this is an inversion
            order1 = pos1[c1] < pos1[c2]  # True if c1 comes before c2 in ranking1
            order2 = pos2[c1] < pos2[c2]  # True if c1 comes before c2 in ranking2
            
            if order1 != order2:
                inversions += 1
    
    return inversions


# Distance metric registry
DISTANCE_METRICS = {
    "spearman": spearman_footrule_distance,
    "kendall_tau": kendall_tau_distance,
    # Future additions can be added here:
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
