"""Core functionality for generating strategic reports that evolve over time."""

from strategies import get_strategy_instance, list_strategies


def generate_strategic_reports(
    honest_reports, 
    T, 
    m, 
    seed=None, 
    rng=None,
    strategy="gt_strategy",
    # GTStrategy parameters
    anchor_strength=0.1,
    learning_rate=0.2,
    sharpness=3.0,
    # SimilarityStrategy parameters (for backward compatibility)
    distance_metric="spearman",
    # Graph topology
    graph=None
):
    """
    Generate strategic reports that evolve over T iterations.
    
    Reports start from honest_reports and evolve based on the selected strategy.
    By default, uses GTStrategy which implements iterative game theory dynamics.
    
    Args:
        honest_reports: List of ranking tuples (baseline honest reports), one per voter
        T: Number of iterations (time steps)
        m: Number of candidates
        seed: Random seed for reproducibility (used if rng is None)
        rng: Optional numpy Generator (if None, creates new one from seed)
        strategy: Strategy name to use (default: "gt_strategy")
                  Available: "gt_strategy", "similarity_strategy"
        
        anchor_strength: Anchoring parameter (0-1), controls how much voters stick to baseline.
                For GTStrategy: Used directly as "anchor_strength" parameter (default: 0.1).
                For SimilarityStrategy: Controls how closely reports stay to honest reports.
                1.0 = reports never change, 0.0 = reports can change completely randomly (default: 0.5)
        learning_rate: Learning rate (0-1) for GTStrategy, controls update speed (default: 0.2)
        sharpness: Sharpness parameter (>0) for GTStrategy, controls exploration vs exploitation.
                  Higher sharpness = more exploitation (sharper distribution, more focused)
                  Lower sharpness = more exploration (flatter distribution, more random) (default: 3.0)
        distance_metric: Name of distance metric for SimilarityStrategy (default: "spearman")
                         Available: "spearman", "kendall_tau"
        graph: Optional igraph.Graph object defining social network topology.
               If None (default), uses complete graph (deg = n-1 for all voters).
               Only used by GTStrategy.
    
    Returns:
        dict with at least the following key:
            "reports": numpy array of shape [n, T+1] where:
                - n is the number of voters
                - Column 0 contains honest reports (initial state)
                - Columns 1..T contain evolved reports at each iteration
                - Each cell contains a ranking index (position in all_rankings)

        For GTStrategy, additional keys may be present, including:
            "selected_probs": numpy array of shape [n, T+1] giving, for each
                voter and time step, the probability mass the internal strategy
                distribution assigns to the selected (most likely) ranking.
    
    Raises:
        ValueError: If strategy name is unknown or parameters are invalid
    """
    available_strategies = list_strategies()
    if strategy not in available_strategies:
        raise ValueError(
            f"Unknown strategy: {strategy}. Available: {available_strategies}"
        )
    
    # Get strategy instance with appropriate parameters
    if strategy == "gt_strategy":
        # Pass parameters directly to GTStrategy
        strategy_instance = get_strategy_instance(
            strategy, 
            anchor_strength=anchor_strength, 
            learning_rate=learning_rate, 
            sharpness=sharpness
        )
        # GTStrategy doesn't use distance_metric in generate_reports
        result = strategy_instance.generate_reports(
            honest_reports, T, m, seed=seed, rng=rng, graph=graph
        )
    elif strategy == "similarity_strategy":
        strategy_instance = get_strategy_instance(
            strategy, 
            distance_metric=distance_metric
        )
        # SimilarityStrategy uses anchor_strength in generate_reports
        result = strategy_instance.generate_reports(
            honest_reports, T, m, seed=seed, rng=rng, anchor_strength=anchor_strength
        )
    else:
        # For any future strategies, try with minimal parameters
        strategy_instance = get_strategy_instance(strategy)
        result = strategy_instance.generate_reports(
            honest_reports, T, m, seed=seed, rng=rng
        )

    # Normalize return type to a dict with at least "reports"
    if isinstance(result, dict):
        return result

    return {"reports": result}
