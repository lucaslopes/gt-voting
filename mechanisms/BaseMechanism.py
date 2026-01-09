"""Base class for aggregation mechanisms."""

from abc import ABC, abstractmethod
import re


class BaseMechanism(ABC):
    """
    Abstract base class for aggregation mechanisms.
    
    All mechanisms must implement the aggregate() method which takes reported rankings
    and returns a probability distribution over candidates.
    """
    
    @property
    def name(self):
        """
        Get the mechanism name in snake_case format.
        
        Converts class name (e.g., "PairwiseMajority") to snake_case (e.g., "pairwise_majority").
        
        Returns:
            str: Mechanism name in snake_case format
        """
        # Convert CamelCase to snake_case
        # Insert underscore before uppercase letters (except the first one)
        name = self.__class__.__name__
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return name
    
    @abstractmethod
    def aggregate(self, reported_rankings):
        """
        Aggregate reported rankings into a probability distribution over candidates.
        
        Args:
            reported_rankings: List of n ranking tuples (e.g., [(0,1,2), (1,0,2), ...])
                              Each ranking is a tuple where earlier positions indicate preference.
                              All rankings must have the same set of candidates.
        
        Returns:
            List of probabilities in candidate order (e.g., [0.4, 0.3, 0.3] for candidates 0, 1, 2)
            - Probabilities must sum to 1.0
            - All probabilities must be non-negative
        
        Raises:
            ValueError: If reported_rankings is empty or rankings are invalid
        """
        pass
    
    def validate_rankings(self, reported_rankings):
        """
        Validate that reported_rankings are valid and consistent.
        
        Args:
            reported_rankings: List of ranking tuples to validate
        
        Raises:
            ValueError: If rankings are empty, invalid, or inconsistent
        
        Returns:
            tuple: (candidates, m, n) where:
                - candidates: List of candidate identifiers
                - m: Number of candidates
                - n: Number of voters
        """
        if not reported_rankings:
            raise ValueError("reported_rankings cannot be empty")
        
        n = len(reported_rankings)
        
        # Extract candidates from first ranking
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
        
        return candidates, m, n
    
    def normalize_probabilities(self, probabilities, candidates):
        """
        Normalize probabilities to ensure they sum to 1.0.
        
        Args:
            probabilities: List or dict of probabilities (may not sum to 1.0)
            candidates: List of candidate identifiers in order
        
        Returns:
            List of normalized probabilities in candidate order
        """
        if isinstance(probabilities, dict):
            # Convert dict to list in candidate order
            prob_list = [probabilities.get(c, 0.0) for c in candidates]
        else:
            prob_list = list(probabilities)
        
        # Normalize to sum to 1.0
        total = sum(prob_list)
        if total == 0:
            # All zeros: return uniform distribution
            return [1.0 / len(candidates)] * len(candidates)
        
        return [p / total for p in prob_list]
