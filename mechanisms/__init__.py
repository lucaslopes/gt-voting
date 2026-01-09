"""Mechanism module for aggregation mechanisms.

This module provides automatic discovery of aggregation mechanisms that inherit
from BaseMechanism. Mechanisms are automatically registered and can be accessed
by their snake_case name (e.g., PairwiseMajority -> "pairwise_majority").
"""

import os
import importlib
import inspect
from pathlib import Path
from mechanisms.BaseMechanism import BaseMechanism


# Registry of available mechanisms: {mechanism_name: mechanism_class}
_MECHANISMS = {}


def _discover_mechanisms():
    """
    Automatically discover all mechanism classes in the mechanisms directory.
    
    Scans the mechanisms/ directory for Python files and imports classes that
    inherit from BaseMechanism. Excludes BaseMechanism itself and __init__.
    """
    mechanisms_dir = Path(__file__).parent
    
    # Get all Python files in the mechanisms directory
    for file_path in mechanisms_dir.glob("*.py"):
        module_name = file_path.stem
        
        # Skip __init__ and BaseMechanism
        if module_name in ("__init__", "BaseMechanism"):
            continue
        
        try:
            # Import the module
            module = importlib.import_module(f"mechanisms.{module_name}")
            
            # Find all classes in the module that inherit from BaseMechanism
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of BaseMechanism but not BaseMechanism itself
                if (issubclass(obj, BaseMechanism) and 
                    obj is not BaseMechanism and
                    obj.__module__ == module.__name__):
                    # Create an instance to get the name property
                    instance = obj()
                    mechanism_name = instance.name
                    _MECHANISMS[mechanism_name] = obj
        except Exception as e:
            # Skip modules that can't be imported (e.g., syntax errors)
            # In production, you might want to log this
            continue


# Discover mechanisms on module import
_discover_mechanisms()


def get_mechanism(mechanism_name):
    """
    Get a mechanism class by name.
    
    Args:
        mechanism_name: Name of the mechanism in snake_case (e.g., "pairwise_majority")
    
    Returns:
        Mechanism class (not instance) that can be instantiated
    
    Raises:
        ValueError: If mechanism_name is not found in the registry
    
    Example:
        >>> MechanismClass = get_mechanism("pairwise_majority")
        >>> mechanism = MechanismClass()
        >>> probs = mechanism.aggregate(rankings)
    """
    if mechanism_name not in _MECHANISMS:
        available = list_mechanisms()
        raise ValueError(f"Unknown aggregation mechanism: {mechanism_name}. "
                        f"Available: {available}")
    return _MECHANISMS[mechanism_name]


def list_mechanisms():
    """
    Get a list of all available mechanism names.
    
    Returns:
        List of mechanism names in snake_case format (e.g., ["pairwise_majority"])
    """
    return sorted(list(_MECHANISMS.keys()))


def get_mechanism_instance(mechanism_name):
    """
    Get an instance of a mechanism by name.
    
    Args:
        mechanism_name: Name of the mechanism in snake_case (e.g., "pairwise_majority")
    
    Returns:
        Mechanism instance ready to use
    
    Raises:
        ValueError: If mechanism_name is not found in the registry
    
    Example:
        >>> mechanism = get_mechanism_instance("pairwise_majority")
        >>> probs = mechanism.aggregate(rankings)
    """
    MechanismClass = get_mechanism(mechanism_name)
    return MechanismClass()


# Export the registry (read-only access)
MECHANISMS = _MECHANISMS.copy()

__all__ = [
    "BaseMechanism",
    "get_mechanism",
    "get_mechanism_instance",
    "list_mechanisms",
    "MECHANISMS",
]
