"""Opt-in aggregation backends for the gtiv Python API.

The legacy Python solver remains the default. The native extension is optional
and is called in-process through PyO3; the facade never launches a subprocess.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import platform
import sys
from pathlib import Path

import numpy as np


class BackendUnavailableError(RuntimeError):
    """The requested backend is missing or cannot implement this request."""


_RUST_MAX_CANDIDATES = 8
_AUTO_DISABLED_REASON = (
    "automatic native dispatch is disabled until parity and performance are "
    "validated against the public main-branch Python implementation"
)


def _native():
    try:
        module = importlib.import_module("gtiv_native")
    except ModuleNotFoundError as exc:
        if exc.name == "gtiv_native":
            return None
        raise BackendUnavailableError(f"gtiv_native could not load: {exc}") from exc
    except ImportError as exc:
        raise BackendUnavailableError(f"gtiv_native could not load: {exc}") from exc
    required = ("aggregate_rankings",)
    if getattr(module, "BACKEND_API_VERSION", None) != 1 or not all(
        callable(getattr(module, name, None)) for name in required
    ):
        raise BackendUnavailableError("gtiv_native has an incompatible interface")
    return module


def _profile(ballots):
    try:
        rows = [tuple(row) for row in ballots]
    except TypeError as exc:
        raise ValueError("ballots must be an iterable of complete rankings") from exc
    if not rows or not rows[0]:
        raise ValueError("at least one nonempty ballot is required")
    candidates = list(rows[0])
    try:
        candidate_set = set(candidates)
        if len(candidate_set) != len(candidates):
            raise ValueError("each ballot must rank each candidate once")
        if any(len(row) != len(candidates) or set(row) != candidate_set for row in rows):
            raise ValueError("ballots must be complete rankings of the same candidates")
        candidate_id = {candidate: index for index, candidate in enumerate(candidates)}
        encoded = [[candidate_id[candidate] for candidate in row] for row in rows]
    except TypeError as exc:
        raise ValueError("candidate labels must be hashable") from exc
    return rows, candidates, encoded


def _selector(value):
    aliases = {
        "lp": "lp",
        "vertex": "vertex",
        "minimum_norm": "minimum_norm",
        "minimum-norm": "minimum_norm",
        "qp-balanced": "minimum_norm",
    }
    try:
        return aliases[value]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "selector must be 'lp', 'vertex', or 'minimum_norm' ('qp-balanced')"
        ) from exc


def _version():
    try:
        return importlib.metadata.version("gtiv")
    except importlib.metadata.PackageNotFoundError:
        return None


def _native_sha256(module):
    filename = getattr(module, "__file__", None) if module is not None else None
    if not filename:
        return None
    try:
        return hashlib.sha256(Path(filename).resolve(strict=True).read_bytes()).hexdigest()
    except OSError:
        return None


def _metadata(requested, used, selector, native, fallback, **extra):
    return {
        "schema_version": 1,
        "backend_requested": requested,
        "backend_used": used,
        "fallback_reason": fallback,
        "selector": selector,
        "distribution": "gtiv",
        "distribution_version": _version(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "native_version": getattr(native, "__version__", None),
        "native_api_version": getattr(native, "BACKEND_API_VERSION", None),
        "native_binary_sha256": _native_sha256(native),
        "native_source_fingerprint_schema": getattr(
            native, "SOURCE_FINGERPRINT_SCHEMA", None
        ),
        "native_source_sha256": getattr(native, "SOURCE_SHA256", None),
        **extra,
    }


def backend_capabilities():
    """Report the optional module, supported selectors, and dispatch policy."""
    try:
        native = _native()
        unavailable_reason = None if native is not None else "gtiv_native is not installed"
    except BackendUnavailableError as exc:
        native, unavailable_reason = None, str(exc)
    return {
        "schema_version": 1,
        "scope": "gtiv",
        "native": {
            "available": native is not None,
            "unavailable_reason": unavailable_reason,
            "version": getattr(native, "__version__", None),
            "api_version": getattr(native, "BACKEND_API_VERSION", None),
        },
        "aggregate_rankings": {
            "python": {"available": True, "selector": "lp"},
            "rust": {
                "available": native is not None,
                "selectors": ["vertex", "minimum_norm"],
                "max_candidates": _RUST_MAX_CANDIDATES,
                "ballots": "complete, unweighted rankings",
                "candidate_order": "first ballot order",
            },
            "auto": {
                "enabled": False,
                "backend_used": "python",
                "reason": _AUTO_DISABLED_REASON,
            },
        },
        "iterative_voting_system": {
            "native_scope": "sampled GT aggregation only; Python retains sampling and updates",
            "expected_score": "not supported by explicit Rust aggregation",
        },
    }


def aggregate_rankings(
    ballots, *, mechanism="GT", backend="python", selector="lp"
):
    """Aggregate rankings and return candidates, probabilities, and provenance.

    Candidate order follows the first ballot, matching the existing Python GT
    implementation. ``python`` uses the current SciPy/HiGHS solver. Explicit
    ``rust`` requires the optional extension and an explicit Rust selector.
    ``auto`` remains on Python until the public-main parity and performance
    gate is complete.
    """
    rows, candidates, encoded = _profile(ballots)
    selector = _selector(selector)
    if backend not in {"python", "rust", "auto"}:
        raise ValueError("backend must be 'python', 'rust', or 'auto'")

    native = None
    fallback = None
    if backend == "python":
        if selector != "lp":
            raise BackendUnavailableError("the Python backend supports selector='lp'")
        used = "python"
    elif backend == "auto":
        if selector != "lp":
            raise BackendUnavailableError(
                "automatic dispatch currently supports selector='lp' only"
            )
        used, fallback = "python", _AUTO_DISABLED_REASON
    else:
        if mechanism != "GT":
            raise BackendUnavailableError("the Rust backend currently supports mechanism='GT' only")
        if selector == "lp":
            raise BackendUnavailableError(
                "Rust does not implement the Python HiGHS 'lp' selector; "
                "request 'vertex' or 'minimum_norm' explicitly"
            )
        if len(candidates) > _RUST_MAX_CANDIDATES:
            raise BackendUnavailableError(
                f"Rust aggregation supports at most {_RUST_MAX_CANDIDATES} candidates"
            )
        native = _native()
        if native is None:
            raise BackendUnavailableError("gtiv_native is not installed")
        used = "rust"

    if used == "python":
        from core.aggregator_core import aggregate_rankings as python_aggregate

        probabilities = python_aggregate(rows, mechanism=mechanism)
        native_details = None
    else:
        native_selector = "vertex" if selector == "vertex" else "minimum_norm"
        native_details = native.aggregate_rankings(
            encoded, len(candidates), native_selector
        )
        probabilities = native_details["probabilities"]

    return {
        "candidates": candidates,
        "probabilities": list(probabilities),
        "native_details": native_details,
        "metadata": _metadata(
            backend,
            used,
            selector,
            native,
            fallback,
            mechanism=mechanism,
            candidate_count=len(candidates),
            voter_count=len(rows),
        ),
    }


__all__ = [
    "BackendUnavailableError",
    "aggregate_rankings",
    "backend_capabilities",
]
