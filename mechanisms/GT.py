"""GT (Game Theory) aggregation mechanism implementing the Rivest-Shen GT voting system."""

import numpy as np
from numba import njit
from scipy.optimize import linprog
from mechanisms.BaseMechanism import BaseMechanism


def solve_gt_game_from_margin_matrix(M, m):
    """
    Solve GT game from margin matrix using linear programming.
    
    Solves max_p min_q p^T M q, which is equivalent to finding the Nash
    equilibrium mixed strategy for the zero-sum game defined by margin matrix M.
    
    This is a shared function used by both GT.aggregate() and GTStrategy.
    
    Args:
        M: Margin matrix, shape [m, m]
        m: Number of candidates
    
    Returns:
        numpy array of shape [m] representing the probability distribution over candidates
    
    Raises:
        ValueError: If linear programming optimization fails
    """
    # Single candidate case
    if m == 1:
        return np.array([1.0])
    
    # LP formulation: Maximize v subject to M^T p >= v * 1, sum(p) = 1, p >= 0
    # Reference: Rivest-Shen paper, Theorem 2
    # For scipy.optimize.linprog (which minimizes), reformulate as:
    # Minimize: -v
    # Subject to: -M^T p + v <= 0, sum(p) = 1, p >= 0, v unbounded
    
    # Variables: [p_0, ..., p_{m-1}, v]
    c = np.zeros(m + 1)
    c[-1] = -1.0  # Minimize -v (maximize v)
    
    # Constraints: M^T p >= v  =>  -M^T p + v <= 0
    A_ub = np.hstack([-M.T, np.ones((m, 1))])
    b_ub = np.zeros(m)
    
    # Equality constraint: sum(p) = 1
    A_eq = np.zeros((1, m + 1))
    A_eq[0, :m] = 1.0
    b_eq = np.array([1.0])
    
    # Bounds: p_i >= 0 for all i, v is unbounded
    bounds = [(0, None) for _ in range(m)] + [(None, None)]
    
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if not res.success:
        raise ValueError(f"Linear programming optimization failed: {res.message}")
    
    # Extract the probability distribution (first m components)
    return res.x[:m]


@njit
def _compute_margin_matrix_numba(rank_positions_array, m, n):
    """
    Numba-optimized computation of margin matrix.
    
    Args:
        rank_positions_array: Array of shape [n, m] where rank_positions_array[v, c] is the
            position of candidate c in ballot v, or -1 if candidate c is not in ballot v
        m: Number of candidates
        n: Number of voters
    
    Returns:
        numpy array of shape [m, m] representing the margin matrix M
        where M[i, j] = (count i > j) - (count j > i)
    """
    M = np.zeros((m, m))
    
    for i in range(m):
        for j in range(m):
            if i == j:
                continue
            
            votes_i_over_j = 0
            votes_j_over_i = 0
            
            # Iterate over all ballots
            for v in range(n):
                # Get positions of candidates i and j in ballot v
                pos_i = rank_positions_array[v, i]
                pos_j = rank_positions_array[v, j]
                
                # Check if both candidates are in the ballot (position >= 0)
                if pos_i >= 0 and pos_j >= 0:
                    if pos_i < pos_j:  # i is preferred over j
                        votes_i_over_j += 1
                    else:  # j is preferred over i
                        votes_j_over_i += 1
            
            M[i, j] = votes_i_over_j - votes_j_over_i
    
    return M


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
        # Convert to numpy array for numba compatibility
        # rank_positions_array[v, c] = position of candidate c in ballot v (or -1 if not present)
        rank_positions_array = np.full((n, m), -1, dtype=np.int32)
        for v, ballot in enumerate(reported_rankings):
            for pos, cand in enumerate(ballot):
                # Find index of candidate in candidates list
                cand_idx = candidates.index(cand)
                rank_positions_array[v, cand_idx] = pos
        
        # Compute the Margin Matrix M using numba-optimized function
        # M[i, j] = (count i > j) - (count j > i)
        M = _compute_margin_matrix_numba(rank_positions_array, m, n)
        
        # Compute Optimal Mixed Strategy using Linear Programming
        p_optimal = solve_gt_game_from_margin_matrix(M, m)
        
        # Return probabilities as a list in candidate order
        # Round to avoid floating point precision issues
        probabilities = [round(float(p_optimal[i]), 6) for i in range(m)]
        
        # Ensure probabilities sum to 1.0 (handle rounding errors)
        total = sum(probabilities)
        if abs(total - 1.0) > 1e-6:
            # Renormalize if there's a significant difference
            probabilities = [p / total for p in probabilities]
        
        return probabilities
