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
