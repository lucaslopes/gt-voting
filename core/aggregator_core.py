"""Core functionality for aggregating reported rankings into probability distributions."""

from mechanisms import get_mechanism


def get_aggregation_function(mechanism_name="GT"):
    """
    Get aggregation function by name from mechanism registry.
    
    This function maintains backward compatibility by returning a function that
    can be called with reported_rankings. Internally, it uses mechanism classes.
    
    Args:
        mechanism_name: Name of the aggregation mechanism (default: "GT")
    
    Returns:
        Aggregation function that takes reported_rankings and returns a list of probabilities
    
    Raises:
        ValueError: If mechanism_name is not in the registry
    """
    # Get the mechanism class
    MechanismClass = get_mechanism(mechanism_name)
    
    # Return a function that instantiates the mechanism and calls aggregate
    def aggregation_function(reported_rankings):
        mechanism = MechanismClass()
        return mechanism.aggregate(reported_rankings)
    
    return aggregation_function


def aggregate_rankings(
    reported_rankings, mechanism="GT", *, backend="python", selector="lp"
):
    """
    Aggregate n reported rankings into a probability distribution over candidates.
    
    This function takes a list of voter rankings and produces a probability distribution
    where each candidate's probability is determined by the specified aggregation mechanism.
    The default mechanism is GT.
    
    Args:
        reported_rankings: List of n ranking tuples (e.g., [(0,1,2), (1,0,2), ...])
                          Each ranking is a tuple where earlier positions indicate preference.
                          All rankings must have the same set of candidates.
        mechanism: Aggregation mechanism name (default: "GT")
        backend: ``python`` (default), explicit ``rust``, or conservative ``auto``.
            Non-default backends return the same probability-list shape.
        selector: Solver selector. ``lp`` preserves the Python HiGHS path; Rust
            requires an explicit ``vertex`` or ``minimum_norm`` selector.
    
    Returns:
        List of probabilities in candidate order (e.g., [0.4, 0.3, 0.3] for candidates 0, 1, 2)
        - Probabilities sum to 1.0
        - All probabilities are non-negative
    
    Raises:
        ValueError: If reported_rankings is empty, rankings are invalid, or mechanism is unknown
    
    Examples:
        >>> # Plurality example (simplest mechanism)
        >>> rankings = [(0, 1, 2), (0, 1, 2), (1, 0, 2)]
        >>> probs = aggregate_rankings(rankings, mechanism="plurality")
        >>> # Candidate 0 is top choice in 2 out of 3 rankings = 2/3
        >>> # Candidate 1 is top choice in 1 out of 3 rankings = 1/3
        >>> # Candidate 2 is top choice in 0 out of 3 rankings = 0/3
        >>> # Result: [0.666..., 0.333..., 0.0]
        
        >>> # Default GT mechanism example
        >>> rankings = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]  # Rock-paper-scissors cycle
        >>> probs = aggregate_rankings(rankings)  # Uses default "GT" mechanism
        >>> # GT finds optimal mixed strategy via linear programming
        >>> # For symmetric cycle: [0.333..., 0.333..., 0.333...]
    """
    # Preserve the historical implementation for every existing default call.
    # The facade imports this function only with default backend arguments.
    if backend != "python" or selector != "lp":
        from core.backends import aggregate_rankings as aggregate_with_backend

        result = aggregate_with_backend(
            reported_rankings,
            mechanism=mechanism,
            backend=backend,
            selector=selector,
        )
        return result["probabilities"]

    if not reported_rankings:
        raise ValueError("reported_rankings cannot be empty")
    
    # Get the mechanism class and instantiate it
    MechanismClass = get_mechanism(mechanism)
    mechanism_instance = MechanismClass()
    
    # Call the aggregate method
    probabilities = mechanism_instance.aggregate(reported_rankings)
    
    # Validate output
    if not probabilities:
        raise ValueError("Aggregation function returned empty probabilities")
    
    # Verify probabilities sum to 1.0 (with small tolerance for floating point)
    prob_sum = sum(probabilities)
    if abs(prob_sum - 1.0) > 1e-10:
        raise ValueError(f"Probabilities must sum to 1.0, got {prob_sum}")
    
    # Verify all probabilities are non-negative
    if any(p < 0 for p in probabilities):
        raise ValueError("All probabilities must be non-negative")
    
    return probabilities
