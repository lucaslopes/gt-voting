"""Pairwise Majority Rule aggregation mechanism."""

from mechanisms.BaseMechanism import BaseMechanism


class PairwiseMajority(BaseMechanism):
    """
    Pairwise Majority Rule aggregation mechanism.
    
    For each pair of candidates, determine which candidate is preferred by a strict majority
    (> n/2) of voters. Each candidate's probability is proportional to the number of
    head-to-head matchups they win.
    """
    
    def aggregate(self, reported_rankings):
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
            >>> mechanism = PairwiseMajority()
            >>> mechanism.aggregate(rankings)
            [0.666..., 0.333..., 0.0]
            # Candidate 0 beats 1 and 2 (2 wins), candidate 1 beats 2 (1 win), candidate 2 beats none (0 wins)
        """
        # Validate rankings and extract candidates
        candidates, m, n = self.validate_rankings(reported_rankings)
        
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
