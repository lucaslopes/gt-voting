import string
from itertools import permutations


def candidate_labels(m):
    """Return candidate labels A, B, C...; extend with double letters if needed."""
    letters = list(string.ascii_uppercase)
    if m <= len(letters):
        return letters[:m]
    labels = []
    labels.extend(letters)
    remaining = m - len(letters)
    # extend with double letters (AA, AB, ...) deterministically
    for first in letters:
        if remaining <= 0:
            break
        for second in letters:
            labels.append(f"{first}{second}")
            remaining -= 1
            if remaining <= 0:
                break
    return labels[:m]


def generate_rankings(m, alphabetical=False):
    """
    Generate all possible rankings for m candidates.
    
    Args:
        m: Number of candidates
        alphabetical: If True, return alphabetical labels; if False, return integer tuples
    
    Returns:
        List of tuples (either integer tuples or alphabetical labels), sorted lexicographically
    """
    # Generate all permutations as integer tuples
    perms = list(permutations(range(m)))
    
    if alphabetical:
        # Convert to alphabetical labels
        labels = candidate_labels(m)
        rankings = [tuple(labels[c] for c in perm) for perm in perms]
    else:
        # Keep as integer tuples
        rankings = perms
    
    # Sort lexicographically
    rankings.sort()
    
    return rankings
