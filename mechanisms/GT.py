"""GT (Game Theory) aggregation mechanism implementing the Rivest-Shen GT voting system."""

import numpy as np
from scipy.optimize import linprog
from mechanisms.BaseMechanism import BaseMechanism


class GT(BaseMechanism):
    """
    GT (Game Theory) aggregation mechanism.
    
    Implements the Rivest-Shen GT voting system, which models the election as a zero-sum
    game and finds the optimal mixed strategy using linear programming. The mechanism
    computes a margin matrix for all pairwise comparisons and solves for the Nash
    equilibrium strategy, which provides the probability distribution over candidates.
    """
    
    @property
    def name(self):
        """
        Get the mechanism name.
        
        Returns:
            str: Mechanism name "gtmechanism"
        """
        return "GT"
    
    def aggregate(self, reported_rankings):
        """
        Aggregate rankings using the GT (Game Theory) voting system.
        
        The GT system:
        1. Computes a margin matrix M where M[i,j] = (votes i > j) - (votes j > i)
        2. Transforms this into a zero-sum game
        3. Finds the optimal mixed strategy using linear programming
        4. Returns the Nash equilibrium probabilities
        
        Args:
            reported_rankings: List of n ranking tuples (e.g., [(0,1,2), (1,0,2), ...])
                              Each ranking is a tuple where earlier positions indicate preference.
                              All rankings must have the same set of candidates.
        
        Returns:
            List of probabilities in candidate order (e.g., [0.4, 0.3, 0.3] for candidates 0, 1, 2)
            - Probabilities sum to 1.0
            - All probabilities are non-negative
        
        Raises:
            ValueError: If reported_rankings is empty, rankings are invalid, or linear programming fails
        
        Example:
            >>> rankings = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]  # Rock-paper-scissors cycle
            >>> mechanism = GTMechanism()
            >>> mechanism.aggregate(rankings)
            [0.333..., 0.333..., 0.333...]  # Equal probabilities for symmetric cycle
        """
        # Validate rankings and extract candidates
        candidates, m, n = self.validate_rankings(reported_rankings)
        
        # Single candidate case
        if m == 1:
            return [1.0]
        
        # Pre-compute rank positions for each ballot to avoid repeated index() calls
        # rank_positions[v][c] = position of candidate c in ballot v (or None if not present)
        # This optimization reduces complexity from O(n * m^3) to O(n * m^2)
        rank_positions = []
        for ballot in reported_rankings:
            # Create a dictionary mapping candidate to position for O(1) lookup
            pos_dict = {cand: pos for pos, cand in enumerate(ballot)}
            rank_positions.append(pos_dict)
        
        # Compute the Margin Matrix M
        # M[i, j] = (count i > j) - (count j > i)
        M = np.zeros((m, m))
        
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                
                cand_i = candidates[i]
                cand_j = candidates[j]
                
                votes_i_over_j = 0
                votes_j_over_i = 0
                
                # Use pre-computed positions for O(1) lookup instead of O(m) index() call
                for pos_dict in rank_positions:
                    # Check if both candidates are in the ballot
                    if cand_i in pos_dict and cand_j in pos_dict:
                        if pos_dict[cand_i] < pos_dict[cand_j]:
                            votes_i_over_j += 1
                        else:
                            votes_j_over_i += 1
                
                M[i, j] = votes_i_over_j - votes_j_over_i
        
        # Compute Optimal Mixed Strategy using Linear Programming
        # Reference: Rivest-Shen paper, Section 6
        # We transform the zero-sum game into a linear program.
        # To use standard LP solvers (which assume variables >= 0),
        # we shift M so all entries are positive.
        
        # Increase every entry in M by some constant value w
        # We pick w such that M_shifted > 0.
        w = np.max(np.abs(M)) + 1.0
        M_shifted = M + w
        
        # The LP Problem:
        # Minimize: sum(p_x)
        # Subject to: M_shifted * p >= 1 (element-wise)
        #             p >= 0
        
        # scipy.optimize.linprog minimizes c @ x subject to A_ub @ x <= b_ub
        # So we set c = ones vector (to minimize sum)
        # And we rearrange constraints: -M_shifted.T @ p <= -1
        
        c = np.ones(m)
        A_ub = -M_shifted.T  # Transpose because we solve for player strategies
        b_ub = -np.ones(m)
        bounds = [(0, None) for _ in range(m)]  # p >= 0
        
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        
        if not res.success:
            raise ValueError(f"Linear programming optimization failed: {res.message}")
        
        # The solution 'p' from this specific LP formulation is unnormalized.
        # The true probabilities are normalized: p* = p / sum(p)
        p_unnormalized = res.x
        p_optimal = p_unnormalized / np.sum(p_unnormalized)
        
        # Return probabilities as a list in candidate order
        # Round to avoid floating point precision issues
        probabilities = [round(float(p_optimal[i]), 6) for i in range(m)]
        
        # Ensure probabilities sum to 1.0 (handle rounding errors)
        total = sum(probabilities)
        if abs(total - 1.0) > 1e-6:
            # Renormalize if there's a significant difference
            probabilities = [p / total for p in probabilities]
        
        return probabilities
