"""Shared utility functions for core modules."""

import numpy as np


def spawn_rng(seed, rng=None):
    """
    Return a numpy Generator; prefer provided rng to keep runs reproducible.
    
    Args:
        seed: Random seed for reproducibility (used if rng is None)
        rng: Optional numpy Generator (if provided, returns this instead of creating new one)
    
    Returns:
        numpy Generator instance
    """
    return rng if rng is not None else np.random.default_rng(seed)
