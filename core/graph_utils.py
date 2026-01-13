"""Graph utilities for parsing edge lists and computing degrees."""

import numpy as np
import igraph


def parse_edge_list(edge_string, n):
    """
    Parse edge list string and create an igraph Graph.
    
    Edge list format: "0-1,1-2,2-0" (dash-separated pairs, comma-separated edges)
    The graph is undirected, so edge "0-1" is equivalent to "1-0".
    
    Args:
        edge_string: String containing edge list in format "u-v,w-x,..."
        n: Number of vertices (voters). Vertex indices must be in range [0, n-1]
    
    Returns:
        igraph.Graph: Undirected graph with n vertices
    
    Raises:
        ValueError: If edge string format is invalid, vertex indices are out of range,
                   or graph structure is invalid
    """
    if not edge_string or not edge_string.strip():
        raise ValueError("Edge string cannot be empty")
    
    # Parse edges
    edges = []
    edge_parts = edge_string.split(',')
    
    for edge_part in edge_parts:
        edge_part = edge_part.strip()
        if not edge_part:
            continue
        
        # Split by dash
        if '-' not in edge_part:
            raise ValueError(f"Invalid edge format: '{edge_part}'. Expected format: 'u-v'")
        
        parts = edge_part.split('-')
        if len(parts) != 2:
            raise ValueError(f"Invalid edge format: '{edge_part}'. Expected exactly one dash")
        
        try:
            u = int(parts[0].strip())
            v = int(parts[1].strip())
        except ValueError as e:
            raise ValueError(f"Invalid vertex index in edge '{edge_part}': {e}")
        
        # Validate vertex indices
        if u < 0 or u >= n:
            raise ValueError(f"Vertex index {u} is out of range [0, {n-1}]")
        if v < 0 or v >= n:
            raise ValueError(f"Vertex index {v} is out of range [0, {n-1}]")
        
        if u == v:
            raise ValueError(f"Self-loops are not allowed: edge '{edge_part}'")
        
        # Add edge (undirected, so we can add (u,v) or (v,u))
        # Normalize to (min, max) to avoid duplicates
        edge = (min(u, v), max(u, v))
        if edge not in edges:
            edges.append(edge)
    
    # Create igraph Graph
    # igraph expects edges as a list of tuples
    graph = igraph.Graph(n=n, edges=edges, directed=False)
    
    return graph


def compute_degrees(graph, n):
    """
    Compute per-voter degrees from graph.
    
    If graph is None, returns array of n-1 (complete graph default).
    Otherwise, returns array with degree for each voter.
    
    Args:
        graph: igraph.Graph object, or None for complete graph
        n: Number of voters
    
    Returns:
        numpy array of shape [n] with degree for each voter
    """
    if graph is None:
        # Complete graph: each voter is connected to all others
        return np.full(n, n - 1, dtype=int)
    
    # Compute degrees from graph
    degrees = np.array(graph.degree(), dtype=int)
    
    # Ensure we have exactly n degrees
    if len(degrees) != n:
        raise ValueError(
            f"Graph has {len(degrees)} vertices, but expected {n} voters. "
            "Graph must have exactly n vertices."
        )
    
    return degrees


def compute_and_store_payoffs(graph, p_tilde, current_rankings, m, all_rankings):
    """
    Compute Layer 1 pairwise payoffs S^uv = <p_tilde, r_v - r_u> for each edge.
    
    Computes payoffs for each edge (u, v) in the graph based on the centered outcome
    p_tilde and current voter rankings. Stores payoffs as edge attribute "payoff" on
    the graph object and returns a dict mapping (u, v) -> payoff value.
    
    Args:
        graph: igraph.Graph object, or None for complete graph. If None, creates
               a temporary complete graph for storage.
        p_tilde: Centered outcome vector, shape [m]. p_tilde = p - (1/m).
        current_rankings: List of n ranking tuples, one per voter. Each tuple
                          represents the ranking that voter is currently using.
        m: Number of candidates
        all_rankings: List of all possible ranking tuples (for converting ranking
                     indices to rank vectors)
    
    Returns:
        dict mapping (u, v) -> payoff value, where (u, v) is an edge tuple.
        Also stores payoffs on graph.es["payoff"] if graph is provided.
    
    Note:
        Rank vectors use 1-based indexing (rank 1 = top preference) to match
        the mathematical notation in the paper. The payoff formula is:
        S^uv = <p_tilde, r_v - r_u>
    """
    n = len(current_rankings)
    
    # Handle complete graph case (graph is None)
    if graph is None:
        # Create temporary complete graph for storage
        graph = igraph.Graph.Full(n, directed=False)
    
    # Create mapping from ranking tuple to rank vector
    # Rank vectors use 1-based indexing: rank 1 = top preference
    ranking_to_rank_vector = {}
    for ranking in all_rankings:
        rank_vector = np.zeros(m)
        for rank_pos, candidate in enumerate(ranking):
            # rank_pos is 0-indexed in Python, but we use 1-based for math
            rank_vector[candidate] = rank_pos + 1
        ranking_to_rank_vector[ranking] = rank_vector
    
    # Compute rank vectors for current rankings
    rank_vectors = []
    for ranking in current_rankings:
        rank_vectors.append(ranking_to_rank_vector[ranking])
    rank_vectors = np.array(rank_vectors)  # Shape: [n, m]
    
    # Compute payoffs for each edge
    payoffs_dict = {}
    payoff_values = []
    
    # Iterate over all edges in the graph
    for edge in graph.es:
        u = edge.source
        v = edge.target
        
        # Get rank vectors for voters u and v
        r_u = rank_vectors[u]
        r_v = rank_vectors[v]
        
        # Difference vector: r_v - r_u
        diff_vu = r_v - r_u
        
        # Calculate payoff: S^uv = <p_tilde, r_v - r_u>
        payoff = np.dot(p_tilde, diff_vu)
        
        # Store in dict (normalize to (min, max) for consistency)
        edge_key = (min(u, v), max(u, v))
        payoffs_dict[edge_key] = payoff
        
        # Store in list for graph edge attribute
        payoff_values.append(payoff)
    
    # Store payoffs as edge attribute on graph
    graph.es["payoff"] = payoff_values
    
    return payoffs_dict
