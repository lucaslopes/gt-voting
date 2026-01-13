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
    
    The LP formulation follows the standard zero-sum game formulation (Theorem 2 in
    the Rivest-Shen paper): maximizes the game value v subject to M^T p >= v * 1,
    where M is the margin matrix, p is the probability distribution, and v is the
    minimum expected payoff (game value).
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
        2. Models the election as a zero-sum game with payoff matrix M
        3. Finds the Nash equilibrium mixed strategy using linear programming
           (standard formulation: maximize v subject to M^T p >= v * 1, sum(p) = 1)
        4. Returns the optimal probability distribution over candidates
        
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
            >>> mechanism = GT()
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
        # Reference: Rivest-Shen paper, Theorem 2
        # Standard zero-sum game LP formulation:
        # Maximize: v (game value)
        # Subject to: M^T p >= v * 1 (element-wise)
        #             sum(p) = 1
        #             p >= 0
        #
        # For scipy.optimize.linprog (which minimizes), we reformulate as:
        # Minimize: -v
        # Subject to: -M^T p + v <= 0 (equivalent to M^T p >= v)
        #             sum(p) = 1
        #             p >= 0, v unbounded
        
        # Variables: x = [p_0, p_1, ..., p_{m-1}, v]
        # Size: m + 1
        
        # Objective: Maximize v -> Minimize -v
        c = np.zeros(m + 1)
        c[-1] = -1.0
        
        # Constraints: M^T p >= v  =>  -M^T p + v <= 0
        # A_ub should be shape (m, m+1)
        # For each row i of M: -sum(M_ij * p_j) + 1*v <= 0
        A_ub = np.hstack([-M.T, np.ones((m, 1))])
        b_ub = np.zeros(m)
        
        # Equality constraint: sum(p) = 1
        # [1, 1, ..., 1, 0] * x = 1
        A_eq = np.zeros((1, m + 1))
        A_eq[0, :m] = 1.0
        b_eq = np.array([1.0])
        
        # Bounds: p_i >= 0 for all i, v is unbounded
        bounds = [(0, None) for _ in range(m)] + [(None, None)]
        
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
        
        if not res.success:
            raise ValueError(f"Linear programming optimization failed: {res.message}")
        
        # Extract the probability distribution (first m components)
        p_optimal = res.x[:m]
        
        # Return probabilities as a list in candidate order
        # Round to avoid floating point precision issues
        probabilities = [round(float(p_optimal[i]), 6) for i in range(m)]
        
        # Ensure probabilities sum to 1.0 (handle rounding errors)
        total = sum(probabilities)
        if abs(total - 1.0) > 1e-6:
            # Renormalize if there's a significant difference
            probabilities = [p / total for p in probabilities]
        
        return probabilities
