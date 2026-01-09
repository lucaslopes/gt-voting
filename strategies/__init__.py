"""Strategy module for voter strategies.

This module provides automatic discovery of voter strategies that inherit
from BaseStrategy. Strategies are automatically registered and can be accessed
by their snake_case name (e.g., SimilarityStrategy -> "similarity_strategy").
"""

import os
import importlib
import inspect
from pathlib import Path
from strategies.BaseStrategy import BaseStrategy


# Registry of available strategies: {strategy_name: strategy_class}
_STRATEGIES = {}


def _discover_strategies():
    """
    Automatically discover all strategy classes in the strategies directory.
    
    Scans the strategies/ directory for Python files and imports classes that
    inherit from BaseStrategy. Excludes BaseStrategy itself and __init__.
    """
    strategies_dir = Path(__file__).parent
    
    # Get all Python files in the strategies directory
    for file_path in strategies_dir.glob("*.py"):
        module_name = file_path.stem
        
        # Skip __init__ and BaseStrategy
        if module_name in ("__init__", "BaseStrategy"):
            continue
        
        try:
            # Import the module
            module = importlib.import_module(f"strategies.{module_name}")
            
            # Find all classes in the module that inherit from BaseStrategy
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of BaseStrategy but not BaseStrategy itself
                if (issubclass(obj, BaseStrategy) and 
                    obj is not BaseStrategy and
                    obj.__module__ == module.__name__):
                    # Create an instance to get the name property
                    # Note: Some strategies may require constructor args, so we try to instantiate
                    # with no args first, and if that fails, we skip (user should use get_strategy_instance)
                    try:
                        instance = obj()
                        strategy_name = instance.name
                        _STRATEGIES[strategy_name] = obj
                    except TypeError:
                        # Strategy requires constructor arguments, register class without instantiating
                        # We'll need to get the name differently - use the class name conversion
                        import re
                        class_name = obj.__name__
                        strategy_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
                        _STRATEGIES[strategy_name] = obj
        except Exception as e:
            # Skip modules that can't be imported (e.g., syntax errors)
            # In production, you might want to log this
            continue


# Discover strategies on module import
_discover_strategies()


def get_strategy(strategy_name):
    """
    Get a strategy class by name.
    
    Args:
        strategy_name: Name of the strategy in snake_case (e.g., "similarity_strategy")
    
    Returns:
        Strategy class (not instance) that can be instantiated
    
    Raises:
        ValueError: If strategy_name is not found in the registry
    
    Example:
        >>> StrategyClass = get_strategy("similarity_strategy")
        >>> strategy = StrategyClass(distance_metric="spearman")
        >>> reports = strategy.generate_reports(honest_reports, T=5, m=3, anchor_strength=0.5)
    """
    if strategy_name not in _STRATEGIES:
        available = list_strategies()
        raise ValueError(f"Unknown strategy: {strategy_name}. "
                        f"Available: {available}")
    return _STRATEGIES[strategy_name]


def list_strategies():
    """
    Get a list of all available strategy names.
    
    Returns:
        List of strategy names in snake_case format (e.g., ["similarity_strategy"])
    """
    return sorted(list(_STRATEGIES.keys()))


def get_strategy_instance(strategy_name, **kwargs):
    """
    Get an instance of a strategy by name with constructor arguments.
    
    Args:
        strategy_name: Name of the strategy in snake_case (e.g., "similarity_strategy")
        **kwargs: Constructor arguments for the strategy (e.g., distance_metric="spearman")
    
    Returns:
        Strategy instance ready to use
    
    Raises:
        ValueError: If strategy_name is not found in the registry
    
    Example:
        >>> strategy = get_strategy_instance("similarity_strategy", distance_metric="spearman")
        >>> reports = strategy.generate_reports(honest_reports, T=5, m=3, anchor_strength=0.5)
    """
    StrategyClass = get_strategy(strategy_name)
    return StrategyClass(**kwargs)


# Export the registry (read-only access)
STRATEGIES = _STRATEGIES.copy()

__all__ = [
    "BaseStrategy",
    "get_strategy",
    "get_strategy_instance",
    "list_strategies",
    "STRATEGIES",
]
