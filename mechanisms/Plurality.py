"""Plurality aggregation mechanism."""

from mechanisms.BaseMechanism import BaseMechanism


class Plurality(BaseMechanism):
    """
    Plurality aggregation mechanism.
    
    Each candidate's probability is proportional to the fraction of voters who ranked
    them as their top choice (first position). The probability of a candidate equals
    the number of times they appear as top1 divided by the total number of voters.
    """
    
    def aggregate(self, reported_rankings):
        """
        Aggregate rankings using Plurality rule.
        
        Each candidate's probability is the fraction of voters who ranked them first.
        If a candidate appears as the top choice in X out of N rankings, their
        probability is X/N.
        
        Args:
            reported_rankings: List of n ranking tuples (e.g., [(0,1,2), (1,0,2), ...])
                              Each ranking is a tuple where earlier positions indicate preference
        
        Returns:
            List of probabilities in candidate order (e.g., [0.4, 0.3, 0.3] for candidates 0, 1, 2)
            - Probabilities sum to 1.0
            - All probabilities are non-negative
        
        Example:
            >>> rankings = [(0, 1, 2), (0, 1, 2), (1, 0, 2)]
            >>> mechanism = Plurality()
            >>> mechanism.aggregate(rankings)
            [0.666..., 0.333..., 0.0]
            # Candidate 0 is top1 in 2 out of 3 rankings = 2/3
            # Candidate 1 is top1 in 1 out of 3 rankings = 1/3
            # Candidate 2 is top1 in 0 out of 3 rankings = 0/3
        """
        # Validate rankings and extract candidates
        candidates, m, n = self.validate_rankings(reported_rankings)
        
        # Single candidate case
        if m == 1:
            return [1.0]
        
        # Count how many times each candidate appears as top1 (first position)
        top1_counts = {candidate: 0 for candidate in candidates}
        
        for ranking in reported_rankings:
            # The first element in each ranking is the top choice
            top_candidate = ranking[0]
            if top_candidate in top1_counts:
                top1_counts[top_candidate] += 1
        
        # Convert counts to probabilities (fraction of voters who ranked each candidate first)
        probabilities = [top1_counts[candidate] / n for candidate in candidates]
        
        return probabilities
