"""Caching utilities for expensive CLI simulations.

This module centralizes:
- Repository root discovery
- Cache directory layout
- Deterministic cache key generation for run folders
- Simple metadata + pickle-based serialization
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import pickle


# Increment when cached data changes shape or its meaning changes.
DASHBOARD_CACHE_SCHEMA_VERSION = 2
PHASE_TRANSITION_CACHE_SCHEMA_VERSION = 2
TERNARY_CACHE_SCHEMA_VERSION = 2
STRATEGIC_REPORTS_CACHE_SCHEMA_VERSION = 1
STRATEGIC_REPORTS_GT_CACHE_SCHEMA_VERSION = 2
PROPORTIONS_CACHE_SCHEMA_VERSION = 1
PROPORTIONS_GT_CACHE_SCHEMA_VERSION = 2
HONEST_REPORTS_CACHE_SCHEMA_VERSION = 1
RANKINGS_CACHE_SCHEMA_VERSION = 1


def _find_repo_root(start: Optional[Path] = None) -> Path:
    """Best-effort repository root detection.

    We walk upwards from ``start`` looking for either ``pyproject.toml`` or
    ``.git``. If neither is found we fall back to ``start.parent``.
    """
    if start is None:
        start = Path(__file__).resolve()

    for parent in (start,) + tuple(start.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent

    return start.parent


def get_command_cache_dir(command: str, root: Optional[Path] = None) -> Path:
    """Return the base cache directory for a CLI command.

    We use the convention: ``data/{command}_runs/``.
    """
    repo_root = _find_repo_root(root)
    return repo_root / "data" / f"{command}_runs"


def get_dashboard_cache_dir(root: Optional[Path] = None) -> Path:
    """Return the base cache directory for dashboard runs."""
    return get_command_cache_dir("dashboard", root=root)


def _stable_json_hash(payload: Dict[str, Any]) -> str:
    key_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(key_json.encode("utf-8")).hexdigest()


def _human_prefix(parts: Iterable[str]) -> str:
    # Keep filenames simple and cross-platform-ish.
    safe = []
    for p in parts:
        p = str(p).strip()
        p = p.replace(" ", "")
        p = p.replace("/", "-")
        p = p.replace("\\", "-")
        p = p.replace(":", "-")
        safe.append(p)
    return "_".join([p for p in safe if p])


def get_run_path(
    *,
    command: str,
    params: Dict[str, Any],
    prefix_parts: Iterable[str],
    root: Optional[Path] = None,
) -> Path:
    """Compute the directory path for a cached run.

    The directory name includes a human-readable prefix + short hash suffix.
    """
    cache_root = get_command_cache_dir(command, root=root)
    digest = _stable_json_hash(params)
    suffix = digest[:8]
    prefix = _human_prefix(prefix_parts)
    return cache_root / f"{prefix}_{suffix}"


def normalize_baselines_str(baselines: Optional[str]) -> Optional[str]:
    """Normalize baselines string for use in cache keys.

    We keep the logical order but strip redundant whitespace so that
    ``\"0*2, 3*2\"`` and ``\"0*2,3*2\"`` map to the same key.
    """
    if baselines is None:
        return None
    parts = [part.strip() for part in baselines.split(",") if part.strip()]
    return ",".join(parts)


@dataclass(frozen=True)
class DashboardParams:
    """Canonical set of parameters that define a dashboard simulation run."""

    n: int
    m: int
    seed: int
    T: int
    learning_rate: float
    sharpness: float
    baselines: Optional[str]  # Normalized string, or None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": int(self.n),
            "m": int(self.m),
            "seed": int(self.seed),
            "T": int(self.T),
            "learning_rate": float(self.learning_rate),
            "sharpness": float(self.sharpness),
            "baselines": self.baselines,
        }


def _dashboard_params_hash(params: DashboardParams) -> Tuple[str, str]:
    """Return (human_prefix, hash_suffix) for a given parameter set."""
    params_dict = params.to_dict()
    key_json = json.dumps(params_dict, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(key_json.encode("utf-8")).hexdigest()
    hash_suffix = digest[:8]

    # Compact, human-readable prefix
    prefix_parts = [
        f"m{params.m}",
        f"n{params.n}",
        f"T{params.T}",
        f"lr{params.learning_rate}",
        f"sh{params.sharpness}",
        f"seed{params.seed}",
    ]
    if params.baselines is not None:
        prefix_parts.append("baselines")

    human_prefix = "_".join(prefix_parts)
    return human_prefix, hash_suffix


def get_dashboard_run_path(params: DashboardParams, root: Optional[Path] = None) -> Path:
    """Compute the directory path for a cached dashboard run."""
    prefix, suffix = _dashboard_params_hash(params)
    cache_root = get_dashboard_cache_dir(root)
    return cache_root / f"{prefix}_{suffix}"


def _get_git_commit(root: Path) -> Optional[str]:
    """Best-effort retrieval of the current git commit hash (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def load_cached_run(
    *,
    command: str,
    params: Dict[str, Any],
    prefix_parts: Iterable[str],
    schema_version: int,
    root: Optional[Path] = None,
) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """Load cached data + metadata for a given command and params.

    Returns (data, metadata) or (None, None) if missing/invalid.
    """
    run_dir = get_run_path(command=command, params=params, prefix_parts=prefix_parts, root=root)
    meta_path = run_dir / "metadata.json"
    data_path = run_dir / "data.pkl"
    if not meta_path.exists() or not data_path.exists():
        return None, None
    try:
        with meta_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
        if metadata.get("schema_version") != schema_version:
            return None, None
        with data_path.open("rb") as f:
            data = pickle.load(f)
        return data, metadata
    except Exception:
        return None, None


def save_cached_run(
    *,
    command: str,
    params: Dict[str, Any],
    prefix_parts: Iterable[str],
    schema_version: int,
    data: Any,
    root: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """Save cached data + metadata for a command run.

    Returns (run_dir, data_path).
    """
    repo_root = _find_repo_root(root)
    # Use the same root input as get_run_path() so root discovery happens only
    # once. In an installed wheel, discovery can fall back to ``core``; passing
    # that result back through discovery would normalize it to ``site-packages``
    # and write to a different path than the CLI reports and later loads.
    run_dir = get_run_path(command=command, params=params, prefix_parts=prefix_parts, root=root)
    os.makedirs(run_dir, exist_ok=True)

    meta_path = run_dir / "metadata.json"
    data_path = run_dir / "data.pkl"

    metadata: Dict[str, Any] = {
        "schema_version": schema_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "params": params,
    }

    git_commit = _get_git_commit(repo_root)
    if git_commit is not None:
        metadata["git_commit"] = git_commit

    with data_path.open("wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)

    return run_dir, data_path


def load_dashboard_cache(
    params: DashboardParams, root: Optional[Path] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Load cached dashboard data and metadata for a given parameter set.

    Returns ``(data, metadata)`` or ``(None, None)`` if no valid cache exists.
    """
    # Back-compat wrapper around generic cached-run loader.
    prefix, suffix = _dashboard_params_hash(params)
    data, metadata = load_cached_run(
        command="dashboard",
        params=params.to_dict(),
        prefix_parts=[f"{prefix}"],  # suffix is part of hash already; keep prefix readable
        schema_version=DASHBOARD_CACHE_SCHEMA_VERSION,
        root=root,
    )
    if isinstance(data, dict):
        return data, metadata
    return None, None


def save_dashboard_cache(
    params: DashboardParams,
    data: Dict[str, Any],
    root: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """Persist dashboard ``data`` and associated metadata to disk.

    Returns ``(run_dir, data_path)``.
    """
    # Back-compat wrapper around generic cached-run saver.
    prefix, _ = _dashboard_params_hash(params)
    return save_cached_run(
        command="dashboard",
        params=params.to_dict(),
        prefix_parts=[prefix],
        schema_version=DASHBOARD_CACHE_SCHEMA_VERSION,
        data=data,
        root=root,
    )

