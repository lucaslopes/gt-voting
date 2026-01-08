"""Core functionality for aggregating reported rankings into probability distributions."""


def pairwise_majority_aggregate(reported_rankings):
    """
    Aggregate rankings using Pairwise Majority Rule.
    
    For each pair of candidates, determine which candidate is preferred by a strict majority
    (> n/2) of voters. Each candidate's probability is proportional to the number of
    head-to-head matchups they win.
    
    Args:
        reported_rankings: List of n ranking tuples (e.g., [(0,1,2), (1,0,2), ...])
                          Each ranking is a tuple where earlier positions indicate preference
    
    Returns:
        List of probabilities in candidate order (e.g., [0.4, 0.3, 0.3] for candidates 0, 1, 2)
        - Probabilities sum to 1.0
        - All probabilities are non-negative
    
    Example:
        >>> rankings = [(0, 1, 2), (0, 1, 2), (1, 0, 2)]
        >>> pairwise_majority_aggregate(rankings)
        [0.666..., 0.333..., 0.0]
        # Candidate 0 beats 1 and 2 (2 wins), candidate 1 beats 2 (1 win), candidate 2 beats none (0 wins)
    """
    if not reported_rankings:
        raise ValueError("reported_rankings cannot be empty")
    
    n = len(reported_rankings)
    
    # Extract candidates from first ranking (assume all rankings have same candidates)
    first_ranking = reported_rankings[0]
    if not first_ranking:
        raise ValueError("rankings cannot be empty")
    
    candidates = list(first_ranking)
    m = len(candidates)
    
    # Validate that all rankings have the same candidates
    for i, ranking in enumerate(reported_rankings):
        if len(ranking) != m:
            raise ValueError(f"Ranking {i} has {len(ranking)} candidates, expected {m}")
        if set(ranking) != set(candidates):
            raise ValueError(f"Ranking {i} has different candidates than the first ranking")
    
    # Single candidate case
    if m == 1:
        return [1.0]
    
    # Count wins for each candidate in pairwise comparisons
    win_counts = {candidate: 0 for candidate in candidates}
    
    # For each pair of candidates (i, j) where i != j
    for i in range(m):
        candidate_i = candidates[i]
        for j in range(i + 1, m):
            candidate_j = candidates[j]
            
            # Count how many voters prefer candidate_i over candidate_j
            prefer_i_count = 0
            prefer_j_count = 0
            
            for ranking in reported_rankings:
                # Find positions of both candidates in this ranking
                pos_i = ranking.index(candidate_i)
                pos_j = ranking.index(candidate_j)
                
                if pos_i < pos_j:
                    prefer_i_count += 1
                elif pos_j < pos_i:
                    prefer_j_count += 1
                # If pos_i == pos_j (shouldn't happen with valid rankings), ignore
            
            # Strict majority: only count as win if > n/2
            majority_threshold = n / 2
            
            if prefer_i_count > majority_threshold:
                win_counts[candidate_i] += 1
            elif prefer_j_count > majority_threshold:
                win_counts[candidate_j] += 1
            # If neither has strict majority (tie), neither gets a win
    
    # Convert win counts to probabilities
    total_wins = sum(win_counts.values())
    
    if total_wins == 0:
        # All ties: return uniform distribution
        return [1.0 / m] * m
    
    # Normalize win counts to probabilities
    probabilities = [win_counts[candidate] / total_wins for candidate in candidates]
    
    return probabilities


# Aggregation mechanism registry
AGGREGATION_MECHANISMS = {
    "pairwise_majority": pairwise_majority_aggregate,
    # Future mechanisms can be added here:
    # "borda_count": borda_count_aggregate,
    # "copeland": copeland_aggregate,
}


def get_aggregation_function(mechanism_name="pairwise_majority"):
    """
    Get aggregation function by name from registry.
    
    Args:
        mechanism_name: Name of the aggregation mechanism (default: "pairwise_majority")
    
    Returns:
        Aggregation function that takes reported_rankings and returns a list of probabilities
    
    Raises:
        ValueError: If mechanism_name is not in the registry
    """
    if mechanism_name not in AGGREGATION_MECHANISMS:
        available = list(AGGREGATION_MECHANISMS.keys())
        raise ValueError(f"Unknown aggregation mechanism: {mechanism_name}. "
                        f"Available: {available}")
    return AGGREGATION_MECHANISMS[mechanism_name]


def aggregate_rankings(reported_rankings, mechanism="pairwise_majority"):
    """
    Aggregate n reported rankings into a probability distribution over candidates.
    
    This function takes a list of voter rankings and produces a probability distribution
    where each candidate's probability is determined by the specified aggregation mechanism.
    The default mechanism is Pairwise Majority Rule.
    
    Args:
        reported_rankings: List of n ranking tuples (e.g., [(0,1,2), (1,0,2), ...])
                          Each ranking is a tuple where earlier positions indicate preference.
                          All rankings must have the same set of candidates.
        mechanism: Aggregation mechanism name (default: "pairwise_majority")
    
    Returns:
        List of probabilities in candidate order (e.g., [0.4, 0.3, 0.3] for candidates 0, 1, 2)
        - Probabilities sum to 1.0
        - All probabilities are non-negative
    
    Raises:
        ValueError: If reported_rankings is empty, rankings are invalid, or mechanism is unknown
    
    Example:
        >>> # Pairwise Majority Rule example
        >>> rankings = [(0, 1, 2), (0, 1, 2), (1, 0, 2), (1, 0, 2), (2, 0, 1)]
        >>> probs = aggregate_rankings(rankings)
        >>> # Candidate 0 beats 1 (3 out of 5) and 2 (3 out of 5) = 2 wins
        >>> # Candidate 1 beats 2 (4 out of 5) = 1 win
        >>> # Candidate 2 beats none = 0 wins
        >>> # Probabilities proportional to wins: [2/3, 1/3, 0]
        
        >>> # All ties example
        >>> rankings = [(0, 1), (1, 0)]
        >>> probs = aggregate_rankings(rankings)
        >>> # Neither candidate has strict majority, so uniform: [0.5, 0.5]
    """
    if not reported_rankings:
        raise ValueError("reported_rankings cannot be empty")
    
    # Get the aggregation function from registry
    aggregate_func = get_aggregation_function(mechanism)
    
    # Call the aggregation function
    probabilities = aggregate_func(reported_rankings)
    
    # Validate output
    if not probabilities:
        raise ValueError("Aggregation function returned empty probabilities")
    
    # Verify probabilities sum to 1.0 (with small tolerance for floating point)
    prob_sum = sum(probabilities)
    if abs(prob_sum - 1.0) > 1e-10:
        raise ValueError(f"Probabilities must sum to 1.0, got {prob_sum}")
    
    # Verify all probabilities are non-negative
    if any(p < 0 for p in probabilities):
        raise ValueError("All probabilities must be non-negative")
    
    return probabilities
