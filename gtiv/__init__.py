"""Public Python API for Game-Theoretic Iterative Voting."""

from core.backends import (
    BackendUnavailableError,
    aggregate_rankings,
    backend_capabilities,
)
from core.strategic_reports import generate_strategic_reports
from core.voting_system import IterativeVotingSystem

__all__ = [
    "BackendUnavailableError",
    "IterativeVotingSystem",
    "aggregate_rankings",
    "backend_capabilities",
    "generate_strategic_reports",
]
