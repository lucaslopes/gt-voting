"""Core iterative voting system implementation."""

import numpy as np
from scipy.optimize import linprog
from itertools import permutations
from core.utils import spawn_rng
from core.graph_utils import compute_degrees
from strategies import get_strategy_instance


class IterativeVotingSystem:
    def __init__(self, m, n, alpha, eta, beta, baselines=None, rng=None, graph=None, 
                 use_expected_score=False, strategy="gt_strategy", mechanism="GT",
                 aggregation_backend="python", aggregation_selector="lp"):
        """
        Initialize iterative voting system.
        
        Args:
            m: Number of candidates
            n: Number of voters
            alpha: Anchoring parameter (0-1)
            eta: Learning rate (0-1)
            beta: Sharpness parameter (>0)
            baselines: Optional baseline permutation indices
            rng: Optional random number generator
            graph: Optional interaction graph
            use_expected_score: If False, sample rankings (Algorithm 1 line 3). If True, use expected margins.
            strategy: Strategy name (default: "gt_strategy") or strategy instance.
                     The strategy defines how voters sample/update their rankings.
            mechanism: Aggregation mechanism name (default: "GT").
                      The mechanism defines how rankings are aggregated into outcomes.
            aggregation_backend: Sampled aggregation backend: ``python`` (default),
                explicit ``rust``, or conservative ``auto``.
            aggregation_selector: Solver selector. ``lp`` preserves the Python
                default; Rust requires ``vertex`` or ``minimum_norm`` explicitly.
        """
        from core.backends import validate_backend_options

        aggregation_selector = validate_backend_options(
            aggregation_backend, aggregation_selector
        )
        if use_expected_score and aggregation_backend == "rust":
            from core.backends import BackendUnavailableError

            raise BackendUnavailableError(
                "Rust aggregation supports sampled rankings only; "
                "use_expected_score must be False"
            )
        if use_expected_score and aggregation_selector != "lp":
            from core.backends import BackendUnavailableError

            raise BackendUnavailableError(
                "expected-score dynamics use the Python margin-matrix solver "
                "and support aggregation_selector='lp' only"
            )
        self.m = m
        self.n = n
        self.alpha = alpha
        self.eta = eta
        self.beta = beta
        self.rng = spawn_rng(None, rng)
        self.graph = graph
        self.use_expected_score = use_expected_score
        self.mechanism = mechanism
        self.aggregation_backend = aggregation_backend
        self.aggregation_selector = aggregation_selector
        self.last_aggregation_metadata = None
        
        # Create or use provided strategy instance
        # Strategy defines the sampling/aggregation logic (e.g., Algorithm 1 line 3)
        if isinstance(strategy, str):
            # Strategy name provided - create instance with appropriate parameters
            # Build parameter dict with common parameter names that strategies might accept
            # Strategies will ignore parameters they don't need (via **kwargs or default args)
            strategy_kwargs = self._build_strategy_kwargs(strategy, alpha, eta, beta, use_expected_score)
            self.strategy = get_strategy_instance(strategy, **strategy_kwargs)
        else:
            # Strategy instance provided directly
            self.strategy = strategy
        
        # Complete graph or a "clique" (all voters are connected to all others)
        # This is kept for backward compatibility, but degrees are computed from graph
        self.adj = np.ones((n, n)) - np.eye(n)
        
        # Permutations
        self.perms = list(permutations(range(m)))
        self.n_perms = len(self.perms)
        
        # Rank vectors: [n_perms, m]
        self.rank_vectors = np.zeros((self.n_perms, m))
        for i, p in enumerate(self.perms):
            for rank, candidate in enumerate(p):
                self.rank_vectors[i, candidate] = rank
        
        # Baselines sampled uniformly (reproducible via rng/seed)
        if baselines is None:
            self.baselines = self.rng.choice(self.n_perms, size=n)
        else:
            self.baselines = np.asarray(baselines)
            
        # Initialize X at baselines with small random perturbations
        # This ensures runs are independent even when baselines are fixed
        # Use a small but meaningful perturbation (0.1% of baseline weight)
        self.x = np.zeros((n, self.n_perms))
        for i, base_idx in enumerate(self.baselines):
            # Start from one-hot at baseline
            self.x[i, base_idx] = 1.0
            # Add small random noise proportional to baseline (0.1% perturbation)
            noise_scale = 0.001
            noise = self.rng.uniform(-noise_scale, noise_scale, size=self.n_perms)
            # Apply noise, ensuring baseline position stays positive
            self.x[i] += noise
            self.x[i] = np.maximum(self.x[i], 0)  # Ensure non-negative
            # Renormalize to ensure it's still a valid probability distribution
            self.x[i] /= np.sum(self.x[i])

        # For visualization tracking
        self.strategy_history = [] # Will store most likely rank for each voter
    
    def _build_strategy_kwargs(self, strategy_name, alpha, eta, beta, use_expected_score):
        """
        Build keyword arguments for strategy instantiation.
        
        This method maps common IterativeVotingSystem parameters (alpha, eta, beta)
        to strategy-specific parameter names. Strategies can accept either:
        - New names: anchor_strength, learning_rate, sharpness
        - Old names: alpha, eta, beta (for backward compatibility)
        
        Args:
            strategy_name: Name of the strategy
            alpha: Anchoring parameter
            eta: Learning rate parameter
            beta: Sharpness parameter
            use_expected_score: Whether to use expected scores
        
        Returns:
            dict: Keyword arguments to pass to strategy constructor
        """
        import inspect
        from strategies import get_strategy
        
        # Get the strategy class to inspect its constructor signature
        StrategyClass = get_strategy(strategy_name)
        sig = inspect.signature(StrategyClass.__init__)
        param_names = set(sig.parameters.keys()) - {'self'}  # Exclude 'self'
        
        # Build kwargs dict - only include parameters the strategy accepts
        kwargs = {}
        
        # Map common parameters to strategy parameter names
        # Try new names first, then fall back to old names for backward compatibility
        if 'anchor_strength' in param_names:
            kwargs['anchor_strength'] = alpha
        elif 'alpha' in param_names:
            kwargs['alpha'] = alpha
        
        if 'learning_rate' in param_names:
            kwargs['learning_rate'] = eta
        elif 'eta' in param_names:
            kwargs['eta'] = eta
        
        if 'sharpness' in param_names:
            kwargs['sharpness'] = beta
        elif 'beta' in param_names:
            kwargs['beta'] = beta
        
        if 'use_expected_score' in param_names:
            kwargs['use_expected_score'] = use_expected_score
        
        return kwargs
        
        # Complete graph or a "clique" (all voters are connected to all others)
        # This is kept for backward compatibility, but degrees are computed from graph
        self.adj = np.ones((n, n)) - np.eye(n)
        
        # Permutations
        self.perms = list(permutations(range(m)))
        self.n_perms = len(self.perms)
        
        # Rank vectors: [n_perms, m]
        self.rank_vectors = np.zeros((self.n_perms, m))
        for i, p in enumerate(self.perms):
            for rank, candidate in enumerate(p):
                self.rank_vectors[i, candidate] = rank
        
        # Baselines sampled uniformly (reproducible via rng/seed)
        if baselines is None:
            self.baselines = self.rng.choice(self.n_perms, size=n)
        else:
            self.baselines = np.asarray(baselines)
            
        # Initialize X at baselines with small random perturbations
        # This ensures runs are independent even when baselines are fixed
        # Use a small but meaningful perturbation (0.1% of baseline weight)
        self.x = np.zeros((n, self.n_perms))
        for i, base_idx in enumerate(self.baselines):
            # Start from one-hot at baseline
            self.x[i, base_idx] = 1.0
            # Add small random noise proportional to baseline (0.1% perturbation)
            noise_scale = 0.001
            noise = self.rng.uniform(-noise_scale, noise_scale, size=self.n_perms)
            # Apply noise, ensuring baseline position stays positive
            self.x[i] += noise
            self.x[i] = np.maximum(self.x[i], 0)  # Ensure non-negative
            # Renormalize to ensure it's still a valid probability distribution
            self.x[i] /= np.sum(self.x[i])

        # For visualization tracking
        self.strategy_history = [] # Will store most likely rank for each voter
        
    def solve_gt_game(self, M):
        # Solves max_p min_q p^T M q
        c = np.zeros(self.m + 1); c[-1] = -1
        A_ub = np.hstack([-M.T, np.ones((self.m, 1))])
        b_ub = np.zeros(self.m)
        A_eq = np.array([[1.0] * self.m + [0.0]]); b_eq = np.array([1.0])
        bounds = [(0, None)] * self.m + [(None, None)]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
        return res.x[:-1] if res.success else np.ones(self.m)/self.m

    def get_margin_matrix_from_probs(self):
        # Expected Margin Matrix calculation (faster/smoother than sampling)
        # M_ab = Sum_i ( Prob(i ranks a > b) - Prob(i ranks b > a) )
        # This is a deterministic approximation for smoother plots
        M = np.zeros((self.m, self.m))
        
        # Precompute pairwise preference for each permutation
        # pairwise_pref[k, a, b] = 1 if a>b in perm k, -1 if b>a
        if not hasattr(self, 'pairwise_pref'):
            self.pairwise_pref = np.zeros((self.n_perms, self.m, self.m))
            for k, p in enumerate(self.perms):
                for a in range(self.m):
                    for b in range(self.m):
                        if a == b: continue
                        if p.index(a) < p.index(b):
                            self.pairwise_pref[k, a, b] = 1
                        else:
                            self.pairwise_pref[k, a, b] = -1
        
        # Aggregate voter strategies
        # X shape: [n, n_perms]
        # Weighted sum of preferences
        # M[a,b] = sum_i sum_k x[i,k] * pref[k,a,b]
        
        # Sum x across voters -> total weight on each perm
        total_x = np.sum(self.x, axis=0) # [n_perms]
        
        # M[a,b] = sum_k total_x[k] * pairwise_pref[k,a,b]
        for a in range(self.m):
            for b in range(self.m):
                M[a,b] = np.sum(total_x * self.pairwise_pref[:, a, b])
                
        return M

    def step(self):
        # 1. Aggregate (Play step - Algorithm 1 line 3)
        # Delegate to GTStrategy to handle sampling/aggregation logic
        if self.use_expected_score:
            # Expected-score variant: use expected margin matrix (deterministic)
            M = self.get_margin_matrix_from_probs()
            p_t = self.solve_gt_game(M)
            if self.aggregation_backend == "auto":
                from core.backends import _metadata

                self.last_aggregation_metadata = _metadata(
                    "auto",
                    "python",
                    "lp",
                    None,
                    "expected-score dynamics use the existing Python margin-matrix solver",
                    mechanism=self.mechanism,
                    candidate_count=self.m,
                    voter_count=self.n,
                )
            else:
                self.last_aggregation_metadata = None
        else:
            # Sampled variant: delegate to GTStrategy._sample_rankings_from_distribution
            # This ensures Algorithm 1 line 3 logic is defined in GTStrategy, not here
            if self.aggregation_backend == "rust":
                from core.backends import require_native_backend

                require_native_backend()
            sampled_rankings = self.strategy._sample_rankings_from_distribution(
                self.x, self.perms, self.rng
            )
            # Aggregate using the specified mechanism (default: GT)
            # The mechanism defines how rankings are aggregated into outcomes
            if (
                self.aggregation_backend == "python"
                and self.aggregation_selector == "lp"
            ):
                from core.aggregator_core import aggregate_rankings

                p_t = np.array(
                    aggregate_rankings(sampled_rankings, mechanism=self.mechanism)
                )
                self.last_aggregation_metadata = None
            else:
                from core.backends import aggregate_rankings as aggregate_with_backend

                aggregate_result = aggregate_with_backend(
                    sampled_rankings,
                    mechanism=self.mechanism,
                    backend=self.aggregation_backend,
                    selector=self.aggregation_selector,
                )
                p_t = np.array(aggregate_result["probabilities"])
                self.last_aggregation_metadata = aggregate_result["metadata"]
        
        p_tilde = p_t - (1.0 / self.m)
        
        # 2. Update Strategies
        # Score s_i(pi) = - deg_i * <p_tilde, r_pi>
        # This implements Term B: -|N(i)| * <p_tilde, r_pi> for each voter i
        # Term A (sum over neighbors' rankings) is constant w.r.t. π and can be ignored
        # due to Softmax translation invariance
        # Compute per-voter degrees from graph (complete graph default if graph is None)
        deg = compute_degrees(self.graph, self.n)
        
        # Precompute dot products: rank_vectors @ p_tilde gives [n_perms]
        dot_products = self.rank_vectors @ p_tilde  # Shape: [n_perms]
        
        # Compute scores for all voters and permutations using broadcasting
        # deg: shape (n,), dot_products: shape (n_perms,)
        # scores: shape (n, n_perms) where scores[i, k] = -deg[i] * <p_tilde, r_k>
        scores = -deg[:, np.newaxis] * dot_products[np.newaxis, :]  # Shape: [n, n_perms]
        
        # Logit response: normalize scores per voter to avoid overflow
        # Subtract max per voter (along permutation axis)
        scores -= np.max(scores, axis=1, keepdims=True)  # Shape: [n, n_perms]
        sbr = np.exp(self.beta * scores)  # Shape: [n, n_perms]
        sbr /= np.sum(sbr, axis=1, keepdims=True)  # Normalize to probability distribution per voter
        
        # Update x for each voter
        for i in range(self.n):
            # Anchor: one-hot vector at baseline permutation
            anchor = np.zeros(self.n_perms)
            anchor[self.baselines[i]] = 1.0
            
            # Update: x[i] = (1 - eta) * x[i] + eta * ((1 - alpha) * sbr[i] + alpha * anchor)
            self.x[i] = (1 - self.eta) * self.x[i] + self.eta * (
                (1 - self.alpha) * sbr[i] + self.alpha * anchor
            )
        
        # Record dominant strategy for heatmap
        # Argmax of x[i]
        current_strategies = np.argmax(self.x, axis=1)
        self.strategy_history.append(current_strategies)
            
        return p_t


def run_full_scenario_for_alpha(alpha, n=15, m=3, eta=0.2, beta=3.0, T=300, seed=0, rng=None, baselines=None, 
                                 use_expected_score=False, strategy="gt_strategy", mechanism="GT"):
    """
    Run a single simulation for a given alpha and return both:
      - strategies: dominant strategy index per voter over time, shape [n, T]
      - perms: permutation list from the underlying system
      - traj: full trajectory of outcome distributions p^t, shape [T, m]
    This helper is used to ensure that the heatmap and ternary plots
    can be driven from the exact same run.
    
    Args:
        use_expected_score: If False (default), sample rankings from probability distributions
                           (Algorithm 1 line 3). If True, use expected margin matrix (deterministic).
        strategy: Strategy name (default: "gt_strategy") or strategy instance.
        mechanism: Aggregation mechanism name (default: "GT").
    """
    rng = spawn_rng(seed, rng)
    sys = IterativeVotingSystem(m=m, n=n, alpha=alpha, eta=eta, beta=beta, rng=rng, baselines=baselines, 
                                use_expected_score=use_expected_score, strategy=strategy, mechanism=mechanism)
    traj = []
    
    for _ in range(T):
        p = sys.step()
        traj.append(p)
    
    strategies = np.array(sys.strategy_history).T  # [n, T]
    return strategies, sys.perms, np.array(traj)
