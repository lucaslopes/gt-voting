"""GT (Game Theory) strategy for evolving voter reports based on iterative game dynamics."""

import numpy as np
from itertools import permutations
from strategies.BaseStrategy import BaseStrategy
from core.aggregator_core import aggregate_rankings
from core.rankings_core import generate_rankings
from core.utils import spawn_rng
from core.graph_utils import compute_degrees


class GTStrategy(BaseStrategy):
    """
    GT (Game Theory) strategy for evolving voter reports.
    
    Implements the iterative game theory voting system where voters strategically
    update their reported rankings over time based on the aggregated outcome.
    Uses logit response dynamics with anchoring to model how agents change their
    rankings throughout time steps.
    
    The strategy maintains a probability distribution over all possible rankings
    for each voter and updates it iteratively based on:
    - The aggregated outcome (p_t) from the GT mechanism
    - Logit response with a sharpness parameter (how "peaked" best responses are)
    - A learning rate controlling how fast distributions change
    - Anchoring to baseline honest reports via an anchoring strength parameter
    """
    
    @property
    def name(self):
        """
        Get the strategy name.
        
        Returns:
            str: Strategy name "gt_strategy"
        """
        return "gt_strategy"
    
    def __init__(self, anchor_strength=0.1, learning_rate=0.2, sharpness=3.0,
                 alpha=None, eta=None, beta=None):
        """
        Initialize GTStrategy with parameters.
        
        Args:
            anchor_strength: Anchoring strength (0-1), controls how strongly voters
                are pulled back toward their honest baseline reports.
                - 1.0 = "stiff spring" to baseline (always report baseline)
                - 0.0 = "no spring" (no anchoring, fully strategic)
            learning_rate: Learning rate (0-1), controls update speed.
                1.0 = full update, 0.0 = no update
            sharpness: Sharpness parameter (>0), controls exploration vs exploitation
                in the logit response.
                Higher sharpness = more exploitation (sharper distribution, more focused)
                Lower sharpness = more exploration (flatter distribution, more random)
            alpha: Alias for anchor_strength (deprecated, use anchor_strength instead)
            eta: Alias for learning_rate (deprecated, use learning_rate instead)
            beta: Alias for sharpness (deprecated, use sharpness instead)
        """
        # Handle backward compatibility aliases
        if alpha is not None:
            anchor_strength = alpha
        if eta is not None:
            learning_rate = eta
        if beta is not None:
            sharpness = beta
        
        if not (0 <= anchor_strength <= 1):
            raise ValueError("anchor_strength must be between 0 and 1")
        if not (0 <= learning_rate <= 1):
            raise ValueError("learning_rate must be between 0 and 1")
        if sharpness <= 0:
            raise ValueError("sharpness must be positive")
        
        # Scalar anchoring strength (the "spring stiffness" toward honest reports)
        self.anchor_strength = anchor_strength
        self.learning_rate = learning_rate
        self.sharpness = sharpness
    
    def generate_reports(self, honest_reports, T, m, seed=None, rng=None, graph=None, **kwargs):
        """
        Generate strategic reports that evolve over T iterations using GT dynamics.
        
        Reports start from honest_reports and evolve based on iterative game theory
        dynamics. At each step:
        1. Sample rankings from current strategy distribution
        2. Aggregate using GT mechanism to get outcome p_t
        3. Compute scores for each permutation based on p_tilde
        4. Update strategy distribution using logit response with anchoring
        
        Args:
            honest_reports: List of ranking tuples (baseline honest reports), one per voter
            T: Number of iterations (time steps)
            m: Number of candidates
            seed: Random seed for reproducibility (used if rng is None)
            rng: Optional numpy Generator (if provided, uses this instead of creating new one)
            graph: Optional igraph.Graph object defining social network topology.
                  If None (default), uses complete graph (deg = n-1 for all voters).
            **kwargs: Additional parameters (not used, for compatibility)
        
        Returns:
            dict with at least the following keys:
                "reports": numpy array of shape [n, T+1] where:
                    - n is the number of voters
                    - Column 0 contains honest reports (initial state)
                    - Columns 1..T contain evolved reports at each iteration
                    - Each cell contains a ranking index (position in all_rankings)
                "selected_probs": numpy array of shape [n, T+1] where:
                    - selected_probs[i, t] is the probability mass that voter i's
                      internal strategy distribution x assigns to their selected
                      (most likely) ranking at time step t.
                    - Column 0 is identically 1.0, since each voter starts with
                      probability 1.0 on their honest baseline ranking.
        
        Raises:
            ValueError: If honest_reports is empty, T < 1, m < 1, or other validation fails
        """
        # Validate parameters
        self.validate_parameters(T, m, **kwargs)
        n, candidates = self.validate_honest_reports(honest_reports, m)
        
        # Initialize RNG
        rng = spawn_rng(seed, rng)
        
        # Get all possible rankings
        all_rankings = self.get_all_rankings(m, alphabetical=False)
        n_perms = len(all_rankings)
        
        # Create mapping from ranking tuple to index
        ranking_to_index = {ranking: idx for idx, ranking in enumerate(all_rankings)}
        
        # Convert honest reports to baseline indices
        baselines = np.array([ranking_to_index[ranking] for ranking in honest_reports])
        
        # Precompute rank vectors for all permutations
        rank_vectors = self._compute_rank_vectors(m, all_rankings)
        
        # Initialize strategy distribution x: [n, n_perms]
        # Each voter starts with probability 1.0 on their baseline ranking
        x = self._initialize_strategy_distribution(n, n_perms, baselines)
        
        # Initialize reports array: [n, T+1]
        # Column 0 will be honest reports, columns 1..T will be evolved reports
        reports = np.zeros((n, T + 1), dtype=int)
        reports[:, 0] = baselines

        # Track probability of the selected (most likely) ranking for each voter and time
        # At t=0, each voter has probability 1.0 on their honest baseline ranking
        selected_probs = np.ones((n, T + 1), dtype=float)
        
        # Compute per-voter degrees from graph (complete graph default if graph is None)
        deg = compute_degrees(graph, n)
        
        # Iterate over T time steps
        for t in range(1, T + 1):
            # Sample rankings from current strategy distribution
            current_rankings = self._sample_rankings_from_distribution(
                x, all_rankings, rng
            )
            
            # Aggregate using GT mechanism to get p_t
            p_t = np.array(aggregate_rankings(current_rankings, mechanism="GT"))
            
            # Compute p_tilde (centered around uniform distribution)
            p_tilde = p_t - (1.0 / m)
            
            # Update strategy distribution
            x = self._update_strategy_distribution(
                x, p_tilde, baselines, rank_vectors, deg
            )
            
            # Record most likely ranking for each voter (argmax of x[i])
            most_likely_indices = np.argmax(x, axis=1)
            reports[:, t] = most_likely_indices

            # Record the probability assigned to the selected (most likely) ranking
            selected_probs[:, t] = x[np.arange(n), most_likely_indices]
        
        return {
            "reports": reports,
            "selected_probs": selected_probs,
        }
    
    def _compute_rank_vectors(self, m, all_rankings):
        """
        Precompute rank vectors for all permutations.
        
        For each permutation k, rank_vectors[k, candidate] = rank position of candidate
        in permutation k (0 = top, m-1 = bottom).
        
        Args:
            m: Number of candidates
            all_rankings: List of all possible ranking tuples
        
        Returns:
            numpy array of shape [n_perms, m] where rank_vectors[k, c] is the rank
            position of candidate c in permutation k
        """
        n_perms = len(all_rankings)
        rank_vectors = np.zeros((n_perms, m))
        
        for k, ranking in enumerate(all_rankings):
            for rank, candidate in enumerate(ranking):
                rank_vectors[k, candidate] = rank
        
        return rank_vectors
    
    def _initialize_strategy_distribution(self, n, n_perms, baselines):
        """
        Initialize strategy distribution x where each voter starts with probability 1.0
        on their baseline ranking.
        
        Args:
            n: Number of voters
            n_perms: Number of possible permutations (m!)
            baselines: Array of baseline ranking indices, shape [n]
        
        Returns:
            numpy array of shape [n, n_perms] where x[i, k] is the probability
            that voter i uses permutation k
        """
        x = np.zeros((n, n_perms))
        for i, base_idx in enumerate(baselines):
            x[i, base_idx] = 1.0
        return x
    
    def _sample_rankings_from_distribution(self, x, all_rankings, rng):
        """
        Sample rankings from probability distribution x.
        
        For each voter i, sample a ranking according to their probability distribution x[i, :].
        
        Args:
            x: Strategy distribution, shape [n, n_perms]
            all_rankings: List of all possible ranking tuples
            rng: numpy Generator for random sampling
        
        Returns:
            List of n ranking tuples sampled from the distribution
        """
        n = x.shape[0]
        n_perms = len(all_rankings)
        sampled_rankings = []
        
        for i in range(n):
            # Sample according to probability distribution x[i, :]
            perm_idx = rng.choice(n_perms, p=x[i, :])
            sampled_rankings.append(all_rankings[perm_idx])
        
        return sampled_rankings
    
    def _update_strategy_distribution(self, x, p_tilde, baselines, rank_vectors, deg):
        """
        Update strategy distribution using logit response dynamics with anchoring.
        
        For each voter i:
        1. Compute scores for each permutation: score[k] = -deg[i] * <p_tilde, r_k>
        2. Apply logit response: for each voter i, convert scores into a distribution
           using a sharpness parameter (higher sharpness = sharper best response).
        3. Update: x[i] = (1 - learning_rate) * x[i] +
              learning_rate * ((1 - anchor_strength) * sbr[i] + anchor_strength * honest_strategy[i])
        
        Args:
            x: Current strategy distribution, shape [n, n_perms]
            p_tilde: Centered outcome distribution, shape [m]
            baselines: Baseline ranking indices, shape [n]
            rank_vectors: Precomputed rank vectors, shape [n_perms, m]
            deg: Array of degrees for each voter, shape [n]
                 Each deg[i] is the degree of voter i in the social network
        
        Returns:
            Updated strategy distribution, shape [n, n_perms]
        """
        n, n_perms = x.shape
        m = len(p_tilde)
        
        # Precompute dot products: rank_vectors @ p_tilde gives [n_perms]
        dot_products = rank_vectors @ p_tilde  # Shape: [n_perms]
        
        # Compute scores for all voters and permutations using broadcasting
        # deg: shape (n,), dot_products: shape (n_perms,)
        # scores: shape (n, n_perms) where scores[i, k] = -deg[i] * <p_tilde, r_k>
        # This implements Term B: -|N(i)| * <p_tilde, r_pi> for each voter i and permutation k
        scores = -deg[:, np.newaxis] * dot_products[np.newaxis, :]  # Shape: [n, n_perms]
        
        # Logit response: normalize scores per voter to avoid overflow
        # Subtract max per voter (along permutation axis)
        scores -= np.max(scores, axis=1, keepdims=True)  # Shape: [n, n_perms]
        # Use sharpness directly: higher sharpness = sharper distribution = more exploitation
        sbr = np.exp(self.sharpness * scores)  # Shape: [n, n_perms]
        sbr /= np.sum(sbr, axis=1, keepdims=True)  # Normalize to probability distribution per voter
        
        # Update strategy distribution for each voter
        x_new = np.zeros_like(x)
        for i in range(n):
            # Honest strategy: one-hot vector at the voter's baseline (honest) ranking
            # This is the "anchor location" in the spring analogy.
            honest_strategy = np.zeros(n_perms)
            honest_strategy[baselines[i]] = 1.0
            
            # Update:
            # Think of a "spring" connecting the current strategy to the honest baseline:
            # - anchor_strength = spring stiffness toward honest_strategy
            # - (1 - anchor_strength) weights the strategic best response
            x_new[i] = (1 - self.learning_rate) * x[i] + self.learning_rate * (
                (1 - self.anchor_strength) * sbr[i] + self.anchor_strength * honest_strategy
            )
        
        return x_new
