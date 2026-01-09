"""Base class for voter strategies."""

from abc import ABC, abstractmethod
import re
from core.rankings_core import generate_rankings


class BaseStrategy(ABC):
    """
    Abstract base class for voter strategies.
    
    All strategies must implement the generate_reports() method which takes honest reports
    and evolves them over T time steps, returning a numpy array of shape [n, T+1] where
    each cell contains a ranking index.
    """
    
    @property
    def name(self):
        """
        Get the strategy name in snake_case format.
        
        Converts class name (e.g., "SimilarityStrategy") to snake_case (e.g., "similarity_strategy").
        
        Returns:
            str: Strategy name in snake_case format
        """
        # Convert CamelCase to snake_case
        # Insert underscore before uppercase letters (except the first one)
        name = self.__class__.__name__
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return name
    
    @abstractmethod
    def generate_reports(self, honest_reports, T, m, seed=None, rng=None, **kwargs):
        """
        Generate strategic reports that evolve over T iterations.
        
        Args:
            honest_reports: List of ranking tuples (baseline honest reports), one per voter
            T: Number of iterations (time steps)
            m: Number of candidates
            seed: Random seed for reproducibility (used if rng is None)
            rng: Optional numpy Generator (if provided, uses this instead of creating new one)
            **kwargs: Strategy-specific parameters (e.g., `anchor_strength`, `learning_rate`, and `sharpness` for GTStrategy)
        
        Returns:
            numpy array of shape [n, T+1] where:
            - n is the number of voters
            - Column 0 contains honest reports (initial state)
            - Columns 1..T contain evolved reports at each iteration
            - Each cell contains a ranking index (position in all_rankings)
        
        Raises:
            ValueError: If honest_reports is empty, T < 1, m < 1, or other validation fails
        """
        pass
    
    def validate_honest_reports(self, honest_reports, m):
        """
        Validate that honest_reports are valid and consistent.
        
        Args:
            honest_reports: List of ranking tuples to validate
            m: Expected number of candidates
        
        Raises:
            ValueError: If reports are empty, invalid, or inconsistent
        
        Returns:
            tuple: (n, candidates) where:
                - n: Number of voters
                - candidates: Set of candidate identifiers
        """
        if not honest_reports:
            raise ValueError("honest_reports cannot be empty")
        
        n = len(honest_reports)
        
        # Extract candidates from first ranking
        first_ranking = honest_reports[0]
        if not first_ranking:
            raise ValueError("rankings cannot be empty")
        
        candidates = set(first_ranking)
        
        # Validate that all rankings have the same candidates and correct length
        for i, ranking in enumerate(honest_reports):
            if len(ranking) != m:
                raise ValueError(f"Ranking {i} has {len(ranking)} candidates, expected {m}")
            if set(ranking) != candidates:
                raise ValueError(f"Ranking {i} has different candidates than the first ranking")
        
        return n, candidates
    
    def validate_parameters(self, T, m, **kwargs):
        """
        Validate common strategy parameters.
        
        Args:
            T: Number of iterations
            m: Number of candidates
            **kwargs: Additional parameters (validated by specific strategies)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if T < 1:
            raise ValueError("T must be at least 1")
        if m < 1:
            raise ValueError("m (number of candidates) must be at least 1")
    
    def get_all_rankings(self, m, alphabetical=False):
        """
        Get all possible rankings for m candidates.
        
        Args:
            m: Number of candidates
            alphabetical: If True, return alphabetical labels; if False, return integer tuples
        
        Returns:
            List of ranking tuples (sorted lexicographically)
        """
        return generate_rankings(m, alphabetical=alphabetical)
