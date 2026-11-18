"""GT (Game Theory) strategy for evolving voter reports based on iterative game dynamics."""

import numpy as np
from itertools import permutations
from numba import njit
from strategies.BaseStrategy import BaseStrategy
from core.aggregator_core import aggregate_rankings, reorder_probabilities
from core.rankings_core import generate_rankings
from core.utils import spawn_rng
from core.graph_utils import compute_degrees, compute_and_store_payoffs
from mechanisms.GT import solve_gt_game_from_margin_matrix


@njit
def _compute_rank_vectors_numba(all_rankings_array, n_perms, m):
    """
    Numba-optimized computation of rank vectors.
    
    Args:
        all_rankings_array: numpy array of shape [n_perms, m] where each row is a ranking
        n_perms: Number of permutations
        m: Number of candidates
    
    Returns:
        numpy array of shape [n_perms, m] where rank_vectors[k, c] is the rank
        position of candidate c in permutation k
    """
    rank_vectors = np.zeros((n_perms, m))
    
    for k in range(n_perms):
        for rank in range(m):
            candidate = all_rankings_array[k, rank]
            rank_vectors[k, candidate] = rank
    
    return rank_vectors


@njit
def _compute_expected_margin_matrix_numba(total_x, pairwise_pref, m, n_perms):
    """
    Numba-optimized computation of expected margin matrix.
    
    Args:
        total_x: Array of shape [n_perms] with total weight on each permutation
        pairwise_pref: Array of shape [n_perms, m, m] with pairwise preferences
        m: Number of candidates
        n_perms: Number of permutations
    
    Returns:
        numpy array of shape [m, m] representing the expected margin matrix
    """
    M = np.zeros((m, m))
    
    # M[a,b] = Σ_k total_x[k] * pairwise_pref[k,a,b]
    for a in range(m):
        for b in range(m):
            if a == b:
                continue
            M[a, b] = np.sum(total_x * pairwise_pref[:, a, b])
    
    return M


@njit
def _compute_scores_sampled_numba(deg, dot_products, n, n_perms):
    """
    Numba-optimized computation of scores for sampled variant.
    
    Args:
        deg: Array of shape [n] with degrees for each voter
        dot_products: Array of shape [n_perms] with dot products <p_tilde, r_k>
        n: Number of voters
        n_perms: Number of permutations
    
    Returns:
        numpy array of shape [n, n_perms] where scores[i, k] = -deg[i] * <p_tilde, r_k>
    """
    scores = np.zeros((n, n_perms))
    for i in range(n):
        for k in range(n_perms):
            scores[i, k] = -deg[i] * dot_products[k]
    return scores


@njit
def _compute_scores_expected_numba(adj, expected_rank_vectors, p_tilde, deg, dot_products, n, n_perms, m):
    """
    Numba-optimized computation of scores for expected-score variant.
    
    Args:
        adj: Adjacency matrix of shape [n, n]
        expected_rank_vectors: Array of shape [n, m] with expected rank vectors
        p_tilde: Array of shape [m] with centered outcome distribution
        deg: Array of shape [n] with degrees for each voter
        dot_products: Array of shape [n_perms] with dot products <p_tilde, r_k>
        n: Number of voters
        n_perms: Number of permutations
        m: Number of candidates
    
    Returns:
        numpy array of shape [n, n_perms] with scores
    """
    # Compute neighbor contribution: Σ_{j:{i,j}∈E} <p̃, E_r_j>
    neighbor_scores = np.zeros(n)
    for i in range(n):
        for j in range(n):
            if adj[i, j] > 0:
                # Compute <p_tilde, expected_rank_vectors[j]>
                dot = 0.0
                for c in range(m):
                    dot += p_tilde[c] * expected_rank_vectors[j, c]
                neighbor_scores[i] += dot
    
    # Compute scores for all voters and permutations
    # scores[i, k] = neighbor_scores[i] - deg[i] * <p_tilde, r_k>
    scores = np.zeros((n, n_perms))
    for i in range(n):
        for k in range(n_perms):
            scores[i, k] = neighbor_scores[i] - deg[i] * dot_products[k]
    
    return scores


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
                 alpha=None, eta=None, beta=None, use_expected_score=False):
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
            use_expected_score: If True, use expected-score variant where realized
                neighbor rankings are replaced by their mixed strategies, yielding
                deterministic dynamics. If False (default), use sampled rankings.
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
        self.use_expected_score = use_expected_score
    
    def generate_reports(self, honest_reports, T, m, seed=None, rng=None, graph=None, **kwargs):
        """
        Generate strategic reports that evolve over T iterations using GT dynamics.
        
        Reports start from honest_reports and evolve based on iterative game theory
        dynamics. At each step:
        1. If use_expected_score=False (default): Sample rankings from current strategy distribution
           If use_expected_score=True: Compute expected margin matrix from mixed strategies
        2. Aggregate using GT mechanism to get outcome p_t
        3. Compute scores for each permutation based on p_tilde
           - If use_expected_score=False: Uses simplified score computation
           - If use_expected_score=True: Uses expected neighbor rank vectors (deterministic)
        4. Update strategy distribution using logit response with anchoring
        
        Args:
            honest_reports: List of ranking tuples (baseline honest reports), one per voter
            T: Number of iterations (time steps 1..T), with t=0 being the initial state.
               Total time steps tracked: T+1 (t=0 to t=T inclusive)
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
                    - Column 0 (t=0) contains honest reports (initial state)
                    - Columns 1..T (t=1..T) contain evolved reports at each iteration
                    - Each cell contains a ranking index (position in all_rankings)
                    - Total time steps: T+1 (t=0 to t=T inclusive)
                "selected_probs": numpy array of shape [n, T+1] where:
                    - selected_probs[i, t] is the probability mass that voter i's
                      internal strategy distribution x assigns to their selected
                      (most likely) ranking at time step t.
                    - Column 0 (t=0) is identically 1.0, since each voter starts with
                      probability 1.0 on their honest baseline ranking.
                "p_history": numpy array of shape [T, m] where:
                    - p_history[t-1] is the instantaneous outcome p^t at time step t
                    - Contains outcomes for t=1..T (not including t=0)
                "p_avg_history": numpy array of shape [T, m] where:
                    - p_avg_history[t-1] is the time-averaged outcome \\hat{p}^t = (1/t) * sum_{tau=1}^t p^tau
                    - Contains time-averaged outcomes for t=1..T (not including t=0)
        
        Raises:
            ValueError: If honest_reports is empty, T < 1, m < 1, or other validation fails
        """
        aggregation_backend = kwargs.pop("aggregation_backend", "python")
        aggregation_selector = kwargs.pop("aggregation_selector", "lp")
        from core.backends import validate_backend_options

        aggregation_selector = validate_backend_options(
            aggregation_backend, aggregation_selector
        )
        if self.use_expected_score and aggregation_backend == "rust":
            from core.backends import BackendUnavailableError

            raise BackendUnavailableError(
                "Rust aggregation supports sampled rankings only; "
                "use_expected_score must be False"
            )
        if self.use_expected_score and aggregation_selector != "lp":
            from core.backends import BackendUnavailableError

            raise BackendUnavailableError(
                "expected-score dynamics use the Python margin-matrix solver "
                "and support selector='lp' only"
            )

        # Validate parameters
        self.validate_parameters(T, m, **kwargs)
        n, candidates = self.validate_honest_reports(honest_reports, m)

        if aggregation_backend == "rust":
            from core.backends import require_native_backend, validate_rust_configuration

            validate_rust_configuration(m)
            require_native_backend()
        
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
        
        # Track instantaneous outcomes p^t and time-averaged outcomes \hat{p}^t
        # p_history[t-1] = p^t (instantaneous outcome at time t, for t=1..T)
        # p_avg_history[t-1] = \hat{p}^t = (1/t) * sum_{tau=1}^t p^tau
        p_history = []
        p_avg_history = []
        p_sum = np.zeros(m, dtype=float)  # Accumulator for time-averaging
        aggregation_metadata = None

        if self.use_expected_score and aggregation_backend == "auto":
            from core.backends import _metadata

            aggregation_metadata = _metadata(
                aggregation_backend,
                "python",
                "lp",
                None,
                "expected-score dynamics use the existing Python margin-matrix solver",
                mechanism="GT",
                candidate_count=m,
                voter_count=n,
            )
        
        # Track payoffs history: payoffs_history[t-1] = payoffs dict at time t (for t=1..T)
        payoffs_history = []
        
        # Compute per-voter degrees from graph (complete graph default if graph is None)
        deg = compute_degrees(graph, n)
        
        # Iterate over T time steps
        for t in range(1, T + 1):
            if self.use_expected_score:
                # Expected-score variant: use expected margin matrix (deterministic)
                M = self._compute_expected_margin_matrix(x, all_rankings, m)
                try:
                    p_t = solve_gt_game_from_margin_matrix(M, m)
                except ValueError:
                    # Fallback to uniform distribution if LP fails
                    p_t = np.ones(m) / m
            else:
                # Sampled variant: sample rankings and aggregate
                current_rankings = self._sample_rankings_from_distribution(
                    x, all_rankings, rng
                )
                if aggregation_backend == "python" and aggregation_selector == "lp":
                    probabilities = aggregate_rankings(current_rankings, mechanism="GT")
                    candidates = current_rankings[0]
                else:
                    from core.backends import aggregate_rankings as aggregate_with_backend

                    aggregate_result = aggregate_with_backend(
                        current_rankings,
                        mechanism="GT",
                        backend=aggregation_backend,
                        selector=aggregation_selector,
                    )
                    probabilities = aggregate_result["probabilities"]
                    candidates = aggregate_result["candidates"]
                    if aggregation_metadata is None:
                        aggregation_metadata = aggregate_result["metadata"]
                p_t = np.array(reorder_probabilities(probabilities, candidates, range(m)))
            
            # Store instantaneous outcome p^t
            p_history.append(p_t.copy())
            
            # Accumulate for time-averaging: p_sum += p^t
            p_sum += p_t
            
            # Compute time-averaged outcome: \hat{p}^t = (1/t) * sum_{tau=1}^t p^tau
            p_avg = p_sum / t
            p_avg_history.append(p_avg.copy())
            
            # Compute p_tilde (centered around uniform distribution)
            p_tilde = p_t - (1.0 / m)
            
            # Compute and store Layer 1 payoffs for this time step
            # Get current rankings (either sampled or most likely)
            if self.use_expected_score:
                # For expected-score variant, use most likely rankings
                most_likely_indices = np.argmax(x, axis=1)
                current_rankings_for_payoffs = [all_rankings[idx] for idx in most_likely_indices]
            else:
                # For sampled variant, use the sampled rankings
                current_rankings_for_payoffs = current_rankings
            
            # Compute payoffs and store on graph edges
            # Note: graph may be None (complete graph), function handles this
            payoffs_dict = compute_and_store_payoffs(
                graph, p_tilde, current_rankings_for_payoffs, m, all_rankings
            )
            payoffs_history.append(payoffs_dict.copy())
            
            # Update strategy distribution
            x = self._update_strategy_distribution(
                x, p_tilde, baselines, rank_vectors, deg, graph=graph
            )
            
            # Record most likely ranking for each voter (argmax of x[i])
            most_likely_indices = np.argmax(x, axis=1)
            reports[:, t] = most_likely_indices

            # Record the probability assigned to the selected (most likely) ranking
            selected_probs[:, t] = x[np.arange(n), most_likely_indices]
        
        result = {
            "reports": reports,
            "selected_probs": selected_probs,
            "p_history": np.array(p_history),  # Shape [T, m]
            "p_avg_history": np.array(p_avg_history),  # Shape [T, m]
            "payoffs_history": payoffs_history,  # List of T dicts, each mapping (u, v) -> payoff
        }
        if aggregation_backend != "python" or aggregation_selector != "lp":
            result["aggregation_metadata"] = aggregation_metadata
        return result
    
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
        # Convert list of tuples to numpy array for numba compatibility
        all_rankings_array = np.array([list(ranking) for ranking in all_rankings])
        rank_vectors = _compute_rank_vectors_numba(all_rankings_array, n_perms, m)
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
    
    def _compute_expected_margin_matrix(self, x, all_rankings, m):
        """
        Compute expected margin matrix from probability distributions.
        
        This is the deterministic variant where we compute the margin matrix
        from expected rankings rather than sampling. For each pair (a, b),
        M[a,b] = Σ_i Σ_k x[i,k] * pref[k,a,b] where pref[k,a,b] = 1 if a>b in perm k, else -1.
        
        Args:
            x: Strategy distribution, shape [n, n_perms]
            all_rankings: List of all possible ranking tuples
            m: Number of candidates
        
        Returns:
            numpy array of shape [m, m] representing the expected margin matrix
        """
        n, n_perms = x.shape
        
        # Precompute pairwise preferences for all permutations
        # pairwise_pref[k, a, b] = 1 if a>b in perm k, -1 if b>a, 0 if a==b
        pairwise_pref = np.zeros((n_perms, m, m))
        for k, ranking in enumerate(all_rankings):
            for a in range(m):
                for b in range(m):
                    if a == b:
                        continue
                    # Find positions in ranking
                    pos_a = ranking.index(a)
                    pos_b = ranking.index(b)
                    if pos_a < pos_b:  # a is preferred over b
                        pairwise_pref[k, a, b] = 1
                    else:  # b is preferred over a
                        pairwise_pref[k, a, b] = -1
        
        # Compute expected margin matrix
        # M[a,b] = Σ_i Σ_k x[i,k] * pairwise_pref[k,a,b]
        # Sum x across voters -> total weight on each permutation
        total_x = np.sum(x, axis=0)  # Shape: [n_perms]
        
        # Use numba-optimized function for the matrix computation
        M = _compute_expected_margin_matrix_numba(total_x, pairwise_pref, m, n_perms)
        
        return M
    
    def _update_strategy_distribution(self, x, p_tilde, baselines, rank_vectors, deg, graph=None):
        """
        Update strategy distribution using logit response dynamics with anchoring.
        
        For each voter i:
        1. Compute scores for each permutation:
           - If use_expected_score=False: score[k] = -deg[i] * <p_tilde, r_k>
           - If use_expected_score=True: score[k] = Σ_{j:{i,j}∈E} <p_tilde, E_r_j - r_k>
             where E_r_j = Σ_σ x_j[σ] * r_σ is the expected rank vector of neighbor j
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
            graph: Optional igraph.Graph object defining social network topology.
                  If None, assumes complete graph. Only used when use_expected_score=True.
        
        Returns:
            Updated strategy distribution, shape [n, n_perms]
        """
        n, n_perms = x.shape
        m = len(p_tilde)
        
        if self.use_expected_score:
            # Expected-score variant: use expected neighbor rank vectors
            # Get adjacency matrix from graph
            if graph is None:
                # Complete graph: all voters are neighbors
                adj = np.ones((n, n)) - np.eye(n)
            else:
                # Get adjacency matrix from igraph Graph
                adj = np.array(graph.get_adjacency().data)
            
            # Compute expected rank vectors for all voters: E_r_i = Σ_σ x_i[σ] * r_σ
            # rank_vectors: [n_perms, m], x: [n, n_perms]
            # expected_rank_vectors: [n, m] where expected_rank_vectors[i] = Σ_k x[i,k] * rank_vectors[k]
            expected_rank_vectors = x @ rank_vectors  # Shape: [n, m]
            
            # Precompute dot products: rank_vectors @ p_tilde gives [n_perms]
            dot_products = rank_vectors @ p_tilde  # Shape: [n_perms]
            
            # Use numba-optimized function for score computation
            scores = _compute_scores_expected_numba(
                adj, expected_rank_vectors, p_tilde, deg, dot_products, n, n_perms, m
            )
        else:
            # Sampled variant: simplified score computation
            # Precompute dot products: rank_vectors @ p_tilde gives [n_perms]
            dot_products = rank_vectors @ p_tilde  # Shape: [n_perms]
            
            # Use numba-optimized function for score computation
            scores = _compute_scores_sampled_numba(deg, dot_products, n, n_perms)
        
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
