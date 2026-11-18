# Project name and terminology

## Name and research scope

The project name is **`gtiv`**, short for **Game-Theoretic Iterative Voting**. It studies **Repeated Maximal Lotteries**: in iterative simulations using the GT mechanism, reported rankings are aggregated into a maximal lottery in each round, and voters' reports can evolve before the next round. Other aggregation mechanisms are also available for comparison.

The theoretical inspiration is the GT method described by Ronald L. Rivest and Emily Shen in [“An Optimal Single-Winner Preferential Voting System Based on Game Theory”](https://people.csail.mit.edu/rivest/pubs/RS10.conference.pdf). Their paper calls the original single-round rule the **GT method** and characterizes it as a special case of maximal-lottery methods when pairwise preference strength is measured by vote margins. **“Repeated Maximal Lotteries” describes this project's iterative study; it is not Rivest and Shen's name for their original rule.**

## Python distribution, command, and repository

The public GitHub repository, Python distribution, and installed command all use the name **`gtiv`**:

| Interface | Name |
| --- | --- |
| GitHub repository | [`lucaslopes/gtiv`](https://github.com/lucaslopes/gtiv) |
| Python distribution | `gtiv` |
| Console command | `gtiv` |

Install from a source checkout with:

```bash
python -m pip install .
```

The unified CLI is implemented in `main.py`; its subcommand modules live in the generic `cli/` and `core/` packages.
