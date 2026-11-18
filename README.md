# Game-Theoretic Iterative Voting

`gtiv` studies **Repeated Maximal Lotteries**: in iterative simulations using the GT mechanism, reported rankings are aggregated into a maximal lottery each round, and strategies can update reports before the next round. The toolkit also includes other aggregation mechanisms for comparison, and it visualizes how outcomes evolve.

Ronald L. Rivest and Emily Shen call their single-round rule the “GT method” and describe it as the special case of maximal-lottery methods based on pairwise vote margins. The iterative research question in `gtiv` is how outcomes evolve when reports respond to each round's lottery. [Rivest and Shen's paper](https://people.csail.mit.edu/rivest/pubs/RS10.conference.pdf) · [Project name and terminology](https://github.com/lucaslopes/gtiv/blob/main/docs/PROJECT_IDENTITY.md)

## Installation

Download the 1.0.0 release candidate wheel from its package CI run. Install it
locally using your usual package index for dependencies.

```bash
python -m pip install ./gtiv-1.0.0rc1-py3-none-any.whl
gtiv --help
```

For development, install from the source checkout:

```bash
python -m pip install -e .
```

The Python distribution and its only installed command are both named `gtiv`. The command launches the same CLI as `python main.py`.

This project is licensed under the GNU General Public License v3 or later; see `LICENSE`.

The optional Rust backend, the public `gtiv` Python imports, and the aggregate
and strategic reports commands are covered in the
[Rust backend guide](https://github.com/lucaslopes/gtiv/blob/main/docs/guides/RUST_BACKEND.md).
Python/SciPy is the default solver.

## CLI Usage

The unified CLI is implemented in `main.py` and provides the `rankings`,
`honest-reports`, `strategic-reports`, `proportions`, `ternary`,
`phase-transition`, `dashboard`, and `aggregate` subcommands.

### Basic Usage

```bash
# Using the installed unified CLI entry point
gtiv <command> [options]

# Running from a source checkout
python main.py <command> [options]

# Or using the individual CLI modules directly
uv run python -m cli.rankings_cli [options]
uv run python -m cli.honest_reports_cli [options]
uv run python -m cli.strategic_reports_cli [options]
uv run python -m cli.proportions_cli [options]
uv run python -m cli.ternary_cli [options]
```

### Cached runs (speeding up repeated plots)

Many commands cache simulation results before plotting. Source checkouts use
`data/*_runs/`, such as `data/dashboard_runs/`. Installed packages store
these folders in the current user's cache directory. Set `GTIV_CACHE_DIR`
to use a different location.

On repeat runs with the **same parameters**, the CLI will load cached results instead of recomputing, and it will print a line like:

- `[cache] <command> hit: <path>`

To ignore the cache and recompute, add:

- `--force-recompute`

### Command: `rankings`

Generate and display all possible candidate rankings for a given number of candidates.

#### Basic Examples

```bash
# Generate all rankings for 3 candidates (integer format, default)
gtiv rankings --m 3

# Generate rankings in alphabetical format (A, B, C, ...)
gtiv rankings --m 3 --alphabetical

# Using --candidates as an alternative to --m
gtiv rankings --candidates 4

# Display rankings with a visual plot
gtiv rankings --m 3 --plot

# Specify plot layout (horizontal, vertical, matrix, or auto)
gtiv rankings --m 3 --plot --layout horizontal
gtiv rankings --m 4 --plot --layout matrix
```

#### Options

- `--m`, `--candidates` (int): Number of candidates (required)
- `--alphabetical` (flag): Output rankings in alphabetical format instead of integer tuples
- `--plot` (flag): Display a visual heatmap of all rankings
- `--save` (flag): Export the plot as a high-quality PDF file (300 DPI). Filename is auto-generated based on parameters (e.g., `rankings_m3_layout_horizontal.pdf`)
- `--layout` (str): Plot layout style - `horizontal`, `vertical`, `matrix`, or `auto` (default: `auto`)

### Command: `honest-reports`

Generate honest reports (voter rankings) from baselines or random seed.

#### Basic Examples

```bash
# Generate honest reports using random seed (default: n=15, m=3, seed=0)
gtiv honest-reports --n 15 --m 3 --seed 42

# Generate with custom number of voters and candidates
gtiv honest-reports --n 20 --m 4 --seed 123

# Using baseline string (old syntax: comma-separated indices)
gtiv honest-reports --n 6 --m 3 --baselines "0,1,2,0,1,2"

# Using baseline string (new syntax: repetition, n inferred automatically)
gtiv honest-reports --m 3 --baselines "0*5,3*5,4*5"

# Output in alphabetical format
gtiv honest-reports --m 3 --baselines "0*5,3*5,4*5" --alphabetical

# Display results with a visual heatmap
gtiv honest-reports --m 3 --baselines "0*5,3*5,4*5" --plot

# Save plot as PDF (can be used with or without --plot)
gtiv honest-reports --m 3 --baselines "0*5,3*5,4*5" --save
```

#### Baseline Syntax

The `--baselines` argument supports two formats:

1. **Old syntax (comma-separated)**: `"0,1,2,0,1,2"` - Each number is a permutation index
2. **New syntax (repetition)**: `"0*5,3*5,4*5"` - `index*count` means repeat `index` `count` times
   - Example: `"0*5,3*5,4*5"` creates 5 voters with index 0, 5 with index 3, and 5 with index 4 (total: 15 voters)
   - When using repetition syntax, `--n` is automatically inferred from the total count

Baseline indices refer to positions in the sorted list of all possible rankings generated by `generate_rankings(m)`.

#### Options

- `--n` (int): Number of voters (default: 15, or inferred from `--baselines` if provided)
- `--m` (int): Number of candidates (default: 3, required to validate baseline indices)
- `--seed` (int): Random seed for reproducibility (default: 0, used when `--baselines` not provided)
- `--baselines` (str): Baseline permutation indices in comma-separated or repetition syntax
- `--alphabetical` (flag): Output rankings in alphabetical format instead of integer tuples
- `--plot` (flag): Display a visual heatmap of voter strategies
- `--save` (flag): Export the plot as a high-quality PDF file (300 DPI). Filename is auto-generated based on parameters (e.g., `honest_reports_m3_n15_seed42.pdf`)

### Command: `strategic-reports`

Generate strategic reports that evolve over T iterations, simulating how voters' reports change over time. Supports multiple strategies including GTStrategy (default, game theory dynamics) and SimilarityStrategy (similarity-based evolution).

#### Basic Examples

```bash
# Basic usage with GTStrategy (default) - T=5 iterations
gtiv strategic-reports --m 3 --n 6 --T 5

# GTStrategy with custom parameters
gtiv strategic-reports --m 3 --n 6 --T 5 --anchor-strength 0.2 --learning-rate 0.3 --sharpness 5.0

# Using SimilarityStrategy (backward compatibility)
gtiv strategic-reports --m 3 --n 6 --T 5 --strategy similarity_strategy --anchor-strength 0.5

# Using baseline string with GTStrategy
gtiv strategic-reports --m 3 --baselines "0*5,3*5,4*5" --T 10

# Output in alphabetical format
gtiv strategic-reports --m 3 --n 6 --T 5 --alphabetical

# Display trajectory visualization over T iterations
gtiv strategic-reports --m 3 --n 6 --T 5 --plot

# Save plot as PDF (can be used with or without --plot)
gtiv strategic-reports --m 3 --n 6 --T 5 --save

# GTStrategy with high anchor strength (strong anchoring to baseline)
gtiv strategic-reports --m 3 --n 6 --T 10 --anchor-strength 0.9 --plot

# GTStrategy with low anchor strength (more strategic adaptation)
gtiv strategic-reports --m 3 --n 6 --T 10 --anchor-strength 0.1 --plot

# GTStrategy with expected-score variant (deterministic dynamics)
gtiv strategic-reports --m 3 --n 6 --T 5 --use-expected-score --plot

# Display Layer 1 payoff analysis for all time steps
gtiv strategic-reports --m 3 --n 6 --T 5 --show-payoffs

# Display payoffs only for the last time step
gtiv strategic-reports --m 3 --n 6 --T 5 --show-payoffs --payoff-time last

# Display payoffs for specific time steps (1-indexed: t=1, t=2, t=5)
gtiv strategic-reports --m 3 --n 6 --T 10 --show-payoffs --payoff-time "1,2,5"

# With custom graph topology and payoff analysis
gtiv strategic-reports --m 3 --n 6 --T 5 --graph "0-1,1-2,2-3,3-4,4-5" --show-payoffs
```

#### Strategies

The `--strategy` parameter selects which strategy to use for evolving reports:

##### GTStrategy (default: `gt_strategy`)

Implements iterative game theory dynamics where voters strategically update their reported rankings based on the aggregated outcome. Uses logit response dynamics with anchoring.

**Parameters:**
- `--anchor-strength` (float, 0-1, default: 0.1): Anchoring strength controlling how much voters stick to their baseline (honest) reports. Accepts `--alpha` as alias.
  - Higher anchor strength (e.g., 0.9): Stiff "spring" to the honest baseline (reports stay close to honest rankings)
  - Lower anchor  strength (e.g., 0.1): Loose spring (reports can move more freely in response to outcomes)
- `--learning-rate` (float, 0-1, default: 0.2): Learning rate controlling update speed. Accepts `--eta` as alias.
  - Higher learning rate: Faster adaptation to new outcomes
  - Lower learning rate: Slower, more gradual changes
- `--sharpness` (float, >0, default: 3.0): Sharpness parameter controlling exploration vs exploitation. Accepts `--beta` as alias.
  - Higher sharpness: More exploitation (sharper best-response distribution, more focused on high-scoring rankings)
  - Lower sharpness: More exploration (flatter distribution, more random exploration)
- `--use-expected-score` (flag, default: False): Use expected-score variant where realized neighbor rankings are replaced by their mixed strategies, yielding deterministic dynamics.
  - **False (default)**: Sampled variant - rankings are sampled from probability distributions at each time step, introducing stochasticity. The same seed may produce different trajectories due to randomness in sampling.
  - **True**: Expected-score variant - uses expected margin matrix computed from mixed strategies, resulting in deterministic dynamics. The same seed always produces the same trajectory. This variant replaces realized neighbor rankings π_j^t with their mixed strategies x_j^{t-1} and computes scores as: s̄_i(π) = Σ_{j:{i,j}∈E} <p̃, E_r_j - r_π> where E_r_j = Σ_σ x_j[σ] * r_σ is the expected rank vector of neighbor j. This yields a deterministic update map on the strategy space X, making the dynamics smoother and easier to analyze.
- `--graph` (str, optional): Edge list defining social network graph. Format: `'0-1,1-2,2-0'` (dash-separated pairs, comma-separated edges). If not provided, uses complete graph (default: all voters connected to all others). Only used when `--strategy=gt_strategy`.
- `--show-payoffs` (flag, default: False): Display Layer 1 payoff analysis (S^uv = <p_tilde, r_v - r_u>) for each edge in the graph. Shows detailed breakdown per edge including rankings, rank vectors, differences, and payoff values. Only available when `--strategy=gt_strategy`. Payoffs are computed once per time step during strategy generation and stored efficiently in the results.
- `--payoff-time` (str, default: "all"): Time step(s) to show payoffs for when `--show-payoffs` is set. Options:
  - `"all"` (default): Show payoffs for all time steps (t=1..T)
  - `"last"`: Show payoffs only for the last time step (t=T)
  - Comma-separated list: Show payoffs for specific time steps (e.g., `"1,2,5"` for t=1, t=2, t=5). Time steps are 1-indexed (t=1..T).

**How it works:**
1. At each time step:
   - **Sampled variant (default)**: 
     - Samples rankings from current strategy distribution x
     - Aggregates sampled rankings using GT mechanism to get outcome p_t
     - Computes scores using simplified formula: s_i(π) = -|N(i)| * <p̃, r_π>
   - **Expected-score variant** (`--use-expected-score`):
     - Computes expected margin matrix M from mixed strategies: M[a,b] = Σ_i Σ_k x[i,k] * pref[k,a,b]
     - Solves GT game deterministically from expected margin matrix to get p_t
     - Computes scores using expected neighbor rank vectors: s̄_i(π) = Σ_{j:{i,j}∈E} <p̃, E_r_j - r_π>
     - This yields deterministic dynamics (no randomness from sampling)
2. Computes scores for each possible ranking based on the outcome p_tilde = p_t - (1/m)
3. Updates each voter's probability distribution over rankings using logit response with sharpness parameter
4. Balances strategic adaptation (based on outcomes) with anchoring to baseline reports

##### SimilarityStrategy (`similarity_strategy`)

Evolves reports based on similarity to honest reports, controlled by an anchor strength parameter and distance metric.

**Parameters:**
- `--anchor-strength` (float, 0-1, default: 0.5): Controls how closely reports stay to honest reports
  - **anchor=1.0**: Reports never change (stay at honest reports throughout all iterations)
  - **anchor=0.0**: Reports can change completely randomly (any ranking is allowed)
  - **Intermediate values**: Reports can change, but only to rankings that are "close enough" based on the distance metric
- `--distance-metric` (str, default: "spearman"): Distance metric for determining similarity
  - **spearman**: Spearman footrule distance - sum of absolute position differences for each candidate between two rankings
    - Example: For rankings `(0, 1, 2)` and `(1, 0, 2)`, distance = |0-1| + |1-0| + |2-2| = 2
    - Maximum distance for m candidates: m²/2 (even m) or (m²-1)/2 (odd m)
  - **kendall_tau**: Kendall Tau distance - number of pairwise disagreements (inversions) between two rankings
    - Counts pairs of candidates that are in different order in the two rankings
    - Example: For rankings `(0, 1, 2)` and `(1, 0, 2)`, distance = 1 (one inversion: candidates 0 and 1 are swapped)
    - Maximum distance for m candidates: m*(m-1)/2

The similarity threshold is calculated as `max_distance = (1 - anchor) * max_possible_distance`, where `max_possible_distance` depends on the chosen distance metric.

#### Options

- `--n` (int): Number of voters (default: 15, or inferred from `--baselines` if provided)
- `--m` (int): Number of candidates (default: 3, required to validate baseline indices)
- `--seed` (int): Random seed for reproducibility (default: 0, used when `--baselines` not provided)
- `--baselines` (str): Baseline permutation indices in comma-separated or repetition syntax (same format as `honest-reports`)
- `--T` (int, required): Number of iterations (time steps) for strategic evolution
- `--strategy` (str): Strategy to use. Available: `gt_strategy` (default), `similarity_strategy`
- `--anchor` (float): Anchoring strength (0-1). Controls how much voters stick to baseline. Accepts `--alpha` as alias. Default: 0.1 for GTStrategy, 0.5 for SimilarityStrategy
- `--learning-rate` (float): Learning rate for GTStrategy (0-1, default: 0.2). Accepts `--eta` as alias. Only used when `--strategy=gt_strategy`
- `--sharpness` (float): Sharpness parameter for GTStrategy (>0, default: 3.0). Accepts `--beta` as alias. Only used when `--strategy=gt_strategy`
- `--use-expected-score` (flag): Use expected-score variant for GTStrategy (deterministic dynamics). Only used when `--strategy=gt_strategy`. Default: False (uses sampled rankings). When enabled, replaces sampled rankings with expected margin matrices computed from mixed strategies, yielding deterministic update dynamics. See Example 14 for usage.
- `--graph` (str, optional): Edge list defining social network graph. Format: `'0-1,1-2,2-0'` (dash-separated pairs, comma-separated edges). If not provided, uses complete graph (default: all voters connected to all others). Only used when `--strategy=gt_strategy`.
- `--show-payoffs` (flag): Display Layer 1 payoff analysis (S^uv = <p_tilde, r_v - r_u>) for each edge. Shows detailed breakdown per edge including rankings, rank vectors, differences, and payoffs. Only available when `--strategy=gt_strategy`. See Example 16 for usage.
- `--payoff-time` (str): Time step(s) to show payoffs for when `--show-payoffs` is set. Options: `"all"` (show all time steps), `"last"` (show only last time step), or comma-separated list of time step indices (e.g., `"1,2,5"`). Time steps are 1-indexed (t=1..T). Default: `"all"`. Only used when `--show-payoffs` is set.
- `--distance-metric` (str): Distance metric for SimilarityStrategy. Available: `spearman` (default), `kendall_tau`. Only used when `--strategy=similarity_strategy`
- `--alphabetical` (flag): Output rankings in alphabetical format instead of integer tuples
- `--plot` (flag): Display a visual heatmap showing voter strategy evolution over T+1 time steps (including initial honest reports)
- `--save` (flag): Export the plot as a high-quality PDF file (300 DPI). Filename is auto-generated based on parameters (e.g., `strategic_reports_m3_T9_lr0.4_sh0.3_as0.2_gt_strategy.pdf`)

### Command: `proportions`

Visualize probability distributions as proportion plots (stacked area charts). This command aggregates reported rankings into probability distributions over candidates and displays them as stacked area charts. It supports both single election outcomes and evolution over T iterations when combined with strategic reports.

#### Basic Examples

```bash
# Single election - visualize probability distribution for one set of rankings
gtiv proportions --m 3 --n 6 --seed 42

# Strategic reports over T iterations with GTStrategy (default) - see how probabilities evolve over time
gtiv proportions --m 3 --n 6 --T 5

# GTStrategy with custom parameters
gtiv proportions --m 3 --n 6 --T 5 --anchor-strength 0.2 --learning-rate 0.3 --sharpness 5.0

# GTStrategy with expected-score variant (deterministic dynamics)
gtiv proportions --m 3 --n 6 --T 10 --use-expected-score --plot

# Using SimilarityStrategy
gtiv proportions --m 3 --n 6 --T 5 --strategy similarity_strategy --anchor-strength 0.5

# With baselines - use specific baseline rankings
gtiv proportions --m 3 --baselines "0*5,3*5,4*5" --T 10

# Custom aggregation mechanism (pairwise majority)
gtiv proportions --m 3 --n 6 --T 5 --mechanism pairwise_majority

# Using plurality mechanism
gtiv proportions --m 3 --n 6 --T 5 --mechanism plurality

# Custom title for the plot
gtiv proportions --m 3 --n 6 --T 5 --title "Election Evolution"

# Show integer labels instead of alphabetical
gtiv proportions --m 3 --n 6 --seed 42 --show-integers

# Save plot as PDF (can be used with or without --plot)
gtiv proportions --m 3 --baselines "0*2,3*2,4*2" --T 9 --plot --learning-rate 0.4 --sharpness 0.3 --anchor-strength 0.2 --save

# Plot time-averaged outcomes (follows learning-in-games convention)
gtiv proportions --m 3 --n 6 --T 10 --time-average --plot

# Show both instantaneous and time-averaged outcomes side-by-side
gtiv proportions --m 3 --n 6 --T 10 --show-both --plot
```

#### Modes

The `proportions` command operates in two modes:

1. **Single Election Mode** (when `--T` is not provided):
   - Generates one set of rankings and aggregates them into a probability distribution
   - Shows a single stacked area chart with candidate probabilities
   - Useful for analyzing a single election outcome

2. **Strategic Reports Mode** (when `--T` is provided):
   - Generates strategic reports that evolve over T iterations
   - Aggregates rankings at each time step to get probability distributions
   - Shows evolution of candidate probabilities over time as a stacked area chart
   - Useful for analyzing how voting outcomes change as voters' strategies evolve

#### Aggregation Mechanisms

The `--mechanism` parameter selects how to aggregate rankings into probabilities. Available mechanisms:

- **GT** (default in `aggregate_rankings`): the GT method models the election as a zero-sum game and finds an optimal mixed strategy using linear programming. It is the margin-based maximal-lottery rule described by Rivest and Shen.
  - Computes a margin matrix M where M[i,j] = (votes i > j) - (votes j > i) for all pairwise comparisons
  - Uses the standard zero-sum game LP formulation (Theorem 2): maximizes game value v subject to M^T p >= v * 1, sum(p) = 1
  - Returns probabilities that represent the optimal mixed strategy (Nash equilibrium), ensuring no candidate can be exploited
  - Particularly effective for handling Condorcet cycles (e.g., rock-paper-scissors scenarios)
  - Example: For a symmetric cycle [(0,1,2), (1,2,0), (2,0,1)], returns equal probabilities [0.333..., 0.333..., 0.333...]

- **pairwise_majority** (default in `proportions` CLI): Pairwise Majority Rule - candidates are ranked by the number of head-to-head matchups they win. Each candidate's probability is proportional to the number of other candidates they beat in pairwise comparisons (strict majority required).
  - For each pair of candidates, determines which candidate is preferred by a strict majority (> n/2) of voters
  - Each candidate's probability is proportional to the number of head-to-head matchups they win
  - Example: If candidate A beats candidates B and C in pairwise comparisons, and candidate B beats C, then probabilities are proportional to [2 wins, 1 win, 0 wins]

- **plurality**: Plurality Rule - each candidate's probability equals the fraction of voters who ranked them as their top choice (first position).
  - Probability = (number of times candidate is top1) / (total number of voters)
  - Simple and intuitive: the more voters rank a candidate first, the higher their probability
  - Example: If candidate A is top1 in 4 out of 10 rankings, their probability is 0.4

#### Options

- `--m` (int): Number of candidates (default: 3)
- `--n` (int): Number of voters (default: 15, or inferred from `--baselines` if provided)
- `--seed` (int): Random seed for reproducibility (default: 0, used when `--baselines` not provided)
- `--baselines` (str): Baseline permutation indices in comma-separated or repetition syntax (same format as `honest-reports`)
- `--T` (int, optional): Number of iterations for strategic reports. If provided, uses strategic reports mode. If not provided, uses single election mode.
- `--strategy` (str): Strategy to use for evolving reports. Only used when `--T` is provided. Available: `gt_strategy` (default), `similarity_strategy`
- `--anchor` (float): Anchoring strength (0-1). Controls how much voters stick to baseline. Accepts `--alpha` as alias. Only used when `--T` is provided. Default: 0.1 for GTStrategy, 0.5 for SimilarityStrategy
- `--learning-rate` (float): Learning rate for GTStrategy (0-1, default: 0.2). Accepts `--eta` as alias. Only used when `--T` is provided and `--strategy=gt_strategy`
- `--sharpness` (float): Sharpness parameter for GTStrategy (>0, default: 3.0). Accepts `--beta` as alias. Only used when `--T` is provided and `--strategy=gt_strategy`
- `--use-expected-score` (flag): Use expected-score variant for GTStrategy (deterministic dynamics). Only used when `--T` is provided and `--strategy=gt_strategy`. Default: False (uses sampled rankings)
- `--distance-metric` (str): Distance metric for SimilarityStrategy. Only used when `--T` is provided and `--strategy=similarity_strategy`. Available: `spearman` (default), `kendall_tau`
- `--mechanism` (str): Aggregation mechanism for converting rankings to probabilities (default: `pairwise_majority`). Available: `GT`, `pairwise_majority`, `plurality`
- `--title` (str): Custom title for the plot
- `--show-integers` (flag): Show candidate integers instead of alphabetical labels in legend
- `--plot` (flag): Display a visual proportion plot (stacked area chart)
- `--save` (flag): Export the plot as a high-quality PDF file (300 DPI). Filename is auto-generated based on parameters (e.g., `proportions_m3_T9_lr0.4_sh0.3_as0.2_GT.pdf` for strategic reports mode, or `proportions_m3_GT.pdf` for single election mode)
- `--time-average` (flag): Plot time-averaged outcomes \hat{p}^t instead of instantaneous outcomes p^t. Only available for strategic reports mode (when `--T` is provided) and when using GTStrategy. Time-averaged outcomes are defined as \hat{p}^t = (1/t) * sum_{tau=1}^t p^tau. This follows the learning-in-games convention where time averages converge even when instantaneous trajectories cycle.
- `--show-both` (flag): Display both instantaneous and time-averaged outcomes side-by-side. Only available for strategic reports mode (when `--T` is provided) and when using GTStrategy. Creates two subplots: left shows instantaneous p^t, right shows time-averaged \hat{p}^t.

### Command: `ternary`

Visualize ternary trajectory plots comparing voting dynamics before and after the phase transition threshold. This command generates side-by-side ternary plots showing how voting outcomes evolve in the probability simplex for m=3 candidates. It automatically computes the phase transition threshold and compares trajectories before and after this critical point.

#### Basic Examples

```bash
# Basic ternary plot (default: n=15, m=3, T=300)
gtiv ternary --plot

# With custom parameters
gtiv ternary --n 15 --m 3 --T 300 --learning-rate 0.2 --sharpness 3.0 --seed 42 --plot

# With baselines
gtiv ternary --m 3 --baselines "0*5,3*5,4*5" --T 300 --plot

# Save as PDF
gtiv ternary --n 15 --m 3 --T 300 --save

# Custom title
gtiv ternary --n 15 --m 3 --T 300 --title "Phase Transition Analysis" --plot
```

#### How It Works

1. **Phase Transition Detection**: The command runs a phase transition experiment to determine the threshold alpha value where voting dynamics change significantly
2. **Threshold Computation**: Finds the alpha value at the steepest drop in distance from the center (fair tie)
3. **Before/After Comparison**: Generates trajectories for:
   - **Before threshold**: Alpha value just before the phase transition (strategic dynamics push outcome away from tie)
   - **After threshold**: Alpha value just after the phase transition (anchoring pulls outcome back toward fair tie)
4. **Visualization**: Creates side-by-side ternary plots showing:
   - **Instantaneous trajectories** (gray, faint): Individual time steps p^t
   - **Running average trajectories** (colored gradient): Cumulative average showing overall trend
   - **Start/end markers**: Red 'x' for start, blue '*' for end of running average

#### Visual Elements

- **Ternary Triangle**: The simplex boundary representing all valid probability distributions for 3 candidates
- **Candidate Labels**: Positioned at triangle vertices (top, right, left)
- **Instantaneous Trajectory**: Gray line with low opacity showing individual time steps
- **Running Average**: Colored gradient (viridis colormap) showing cumulative average over time
- **Markers**: Start (red 'x') and end (blue '*') of the running average trajectory

#### Options

- `--n` (int): Number of voters (default: 15, or inferred from `--baselines` if provided)
- `--m` (int): Number of candidates (default: 3, **must be 3** for ternary plots)
- `--seed` (int): Random seed for reproducibility (default: 0, used when `--baselines` not provided)
- `--baselines` (str): Baseline permutation indices in comma-separated or repetition syntax (same format as `honest-reports`)
- `--T` (int): Total number of time steps (default: 300)
- `--learning-rate` (float): Learning rate for GTStrategy (0-1, default: 0.2). Accepts `--eta` as alias
- `--sharpness` (float): Sharpness parameter for GTStrategy (>0, default: 3.0). Accepts `--beta` as alias
- `--title` (str): Custom title for the plot
- `--plot` (flag): Display a visual ternary trajectory plot
- `--save` (flag): Export the plot as a high-quality PDF file (300 DPI). Filename is auto-generated based on parameters (e.g., `ternary_m3_n15_T300_lr0.2_sh3.0_seed0.pdf`)

**Note**: Ternary plots require `m=3` (three candidates). The command will raise an error if `m != 3`.

### Command: `phase-transition`

Visualize the phase transition experiment showing how the distance from the center (fair tie) changes as a function of the anchoring parameter α. The plot includes confidence intervals computed from multiple independent runs.

#### Basic Examples

```bash
# Basic phase transition plot (default: 10 runs per alpha)
gtiv phase-transition --m 3 --n 15 --plot

# With custom parameters
gtiv phase-transition --m 3 --n 15 --runs 20 --burn-in 300 --collection-steps 100 --plot

# With baselines
gtiv phase-transition --m 3 --baselines "0*5,3*5,4*5" --runs 15 --plot

# Save as PDF
gtiv phase-transition --m 3 --n 15 --save
```

#### How It Works

1. **Multiple Runs**: For each alpha value, run `runs` independent simulations
2. **Burn-in Phase**: Run simulation for `burn-in` steps to reach convergence
3. **Collection Phase**: Collect `collection-steps` outcomes and average them
4. **Statistics**: Compute mean and standard deviation across all runs
5. **Visualization**: Plot mean distance with confidence intervals (error bars and/or shaded region)

#### Methodology

- **Burn-in**: Allows the system to reach steady state before measurement
- **Collection**: Averages multiple steps after convergence to smooth fluctuations
- **Multiple Runs**: Provides statistical robustness and confidence intervals
- **Threshold Detection**: Identifies the alpha value where distance drops sharply

#### Visual Elements

- **Mean Line**: Teal line showing average distance across runs
- **Confidence Intervals**: Shaded region (mean ± 1 std) and error bars showing statistical variability
- **Threshold Line**: Dashed gray vertical line marking the phase transition threshold
- **Warped X-axis**: Nonlinear transform near threshold to highlight the transition region

#### Options

- `--n` (int): Number of voters (default: 15, or inferred from `--baselines` if provided)
- `--m` (int): Number of candidates (default: 3)
- `--burn-in` (int): Burn-in steps before collection (default: 200)
- `--collection-steps` (int): Steps to collect and average (default: 50)
- `--runs` (int): Number of independent runs per alpha (default: 10)
- `--learning-rate` (float): Learning rate parameter (default: 0.2)
- `--sharpness` (float): Sharpness parameter (default: 3.0)
- `--seed` (int): Random seed (default: 0)
- `--baselines` (str): Baseline permutation indices in comma-separated or repetition syntax
- `--title` (str): Custom title for the plot
- `--plot` (flag): Display the plot
- `--save` (flag): Export the plot as a high-quality PDF file

## Examples

### Example 1: List All Rankings for 3 Candidates

```bash
gtiv rankings --m 3
```

Output:
```
(0, 1, 2)
(0, 2, 1)
(1, 0, 2)
(1, 2, 0)
(2, 0, 1)
(2, 1, 0)
```

### Example 2: Generate Honest Reports with Specific Baselines

```bash
gtiv honest-reports --m 3 --baselines "0*5,1*5,2*5" --alphabetical
```

This creates 15 voters (5 for each of the first 3 permutation indices) and outputs in alphabetical format.

### Example 3: Visualize Rankings

```bash
gtiv rankings --m 3 --plot --layout horizontal
```

This displays a colorful heatmap showing all possible rankings for 3 candidates.

### Example 3b: Save Rankings Plot as PDF

```bash
gtiv rankings --m 3 --save --layout horizontal
```

This generates and saves the rankings plot as a high-quality PDF file (e.g., `rankings_m3_layout_horizontal.pdf`).

### Example 4: Generate and Visualize Honest Reports

```bash
gtiv honest-reports --n 10 --m 3 --seed 42 --plot
```

This generates 10 random honest reports and displays them as a heatmap.

### Example 4b: Save Honest Reports Plot as PDF

```bash
gtiv honest-reports --n 10 --m 3 --seed 42 --save
```

This generates honest reports and saves the plot as a PDF file (e.g., `honest_reports_m3_n10_seed42.pdf`).

### Example 5: Simulate Strategic Voting Evolution with GTStrategy

```bash
gtiv strategic-reports --m 3 --n 6 --T 5 --plot
```

This simulates how 6 voters' reports evolve over 5 iterations using GTStrategy (default), showing the trajectory in a heatmap where each column represents a time step.

### Example 5b: Save Strategic Reports Plot as PDF

```bash
gtiv strategic-reports --m 3 --baselines "0*2,3*2,4*2" --T 9 --plot --learning-rate 0.4 --sharpness 0.3 --anchor-strength 0.2 --save
```

This generates strategic reports and saves the plot as a PDF file (e.g., `strategic_reports_m3_T9_lr0.4_sh0.3_as0.2_gt_strategy.pdf`).

### Example 6: GTStrategy with Custom Parameters

```bash
gtiv strategic-reports --m 3 --baselines "0*5,1*5,2*5" --T 10 --anchor-strength 0.2 --learning-rate 0.3 --sharpness 5.0 --plot
```

This shows how reports evolve with GTStrategy using custom parameters: anchor=0.2 (moderate anchoring), learning-rate=0.3 (faster learning), sharpness=5.0 (more exploitation, sharper best responses).

### Example 7: GTStrategy with High Anchor strength (Strong Anchoring)

```bash
gtiv strategic-reports --m 3 --n 10 --T 10 --anchor-strength 0.9 --seed 42 --plot
```

This demonstrates GTStrategy with high anchor strength (0.9), meaning voters strongly anchor to their baseline reports while still adapting strategically.

### Example 8: Using SimilarityStrategy (Backward Compatibility)

```bash
gtiv strategic-reports --m 3 --n 6 --T 5 --strategy similarity_strategy --anchor-strength 0.5 --plot
```

This uses SimilarityStrategy with anchor_strength=0.5, demonstrating the similarity-based evolution approach.

### Example 9: SimilarityStrategy with Kendall Tau Distance

```bash
gtiv strategic-reports --m 3 --n 6 --T 5 --strategy similarity_strategy --anchor-strength 0.5 --distance-metric kendall_tau --plot
```

This uses SimilarityStrategy with Kendall Tau distance instead of Spearman footrule to measure similarity between rankings, which may produce different evolution patterns.

### Example 9: Visualize Single Election Probability Distribution

```bash
gtiv proportions --m 3 --n 6 --seed 42 --plot
```

This generates 6 voters' rankings and displays a proportion plot showing the probability distribution over the 3 candidates using Pairwise Majority Rule (default mechanism for `proportions` command).

### Example 9b: Save Proportions Plot as PDF

```bash
gtiv proportions --m 3 --baselines "0*2,3*2,4*2" --T 9 --plot --learning-rate 0.4 --sharpness 0.3 --anchor-strength 0.2 --save
```

This generates strategic reports and saves the proportion plot as a PDF file (e.g., `proportions_m3_T9_lr0.4_sh0.3_as0.2_GT.pdf`).

### Example 10: Visualize Probability Evolution Over Time

```bash
gtiv proportions --m 3 --n 6 --T 5 --plot
```

This simulates strategic voting over 5 iterations using GTStrategy (default) and shows how candidate probabilities evolve over time in a stacked area chart.

### Example 11: Probability Evolution with Baselines

```bash
gtiv proportions --m 3 --baselines "0*5,3*5,4*5" --T 10 --anchor-strength 0.2 --learning-rate 0.3 --sharpness 5.0 --plot
```

This creates 15 voters with specific baseline rankings and shows how their probabilities evolve over 10 time steps.

### Example 12: Compare Different Aggregation Mechanisms

```bash
# GT mechanism (Game Theory)
gtiv proportions --m 3 --n 6 --seed 42 --mechanism GT

# Pairwise Majority Rule
gtiv proportions --m 3 --n 6 --seed 42 --mechanism pairwise_majority

# Plurality Rule
gtiv proportions --m 3 --n 6 --seed 42 --mechanism plurality
```

This demonstrates how different aggregation mechanisms can produce different probability distributions from the same set of rankings.

### Example 13: Time-Averaged Outcomes (Learning-in-Games Convention)

```bash
# Plot time-averaged outcomes instead of instantaneous
gtiv proportions --m 3 --n 6 --T 20 --time-average --plot

# Compare instantaneous vs time-averaged side-by-side
gtiv proportions --m 3 --n 6 --T 20 --show-both --plot --save
```

Time-averaged outcomes \hat{p}^t = (1/t) * sum_{tau=1}^t p^tau follow the learning-in-games convention where time averages converge even when instantaneous trajectories cycle. This is particularly relevant for zero-sum games where many learning dynamics exhibit convergence of time averages rather than pointwise convergence.

### Example 14: Expected-Score Variant (Deterministic Dynamics)

```bash
# Use expected-score variant for deterministic dynamics
gtiv strategic-reports --m 3 --n 6 --T 10 --use-expected-score --plot

# Compare sampled vs expected-score variants
gtiv strategic-reports --m 3 --n 6 --T 10 --seed 42 --plot
gtiv strategic-reports --m 3 --n 6 --T 10 --seed 42 --use-expected-score --plot
```

The expected-score variant replaces sampled rankings with expected margin matrices computed from mixed strategies, resulting in deterministic dynamics. Key differences:

- **Deterministic**: Same seed always produces the same trajectory (no randomness from sampling)
- **Smoother dynamics**: Expected values eliminate stochastic fluctuations, making trajectories easier to analyze
- **Mathematical analysis**: The deterministic update map facilitates theoretical analysis (see paper, lines 448-459)
- **Computational**: Uses expected margin matrix computation instead of sampling, which can be faster for large systems

This variant is particularly useful for:
- Analyzing convergence properties and fixed points
- Comparing theoretical predictions with simulations
- Producing reproducible, deterministic visualizations
- Studying the deterministic update map on the strategy space X

### Example 15: Ternary Trajectory Plot (Phase Transition)

```bash
# Basic ternary plot showing before/after threshold dynamics
gtiv ternary --n 15 --m 3 --T 300 --plot

# With custom parameters
gtiv ternary --n 15 --m 3 --T 300 --learning-rate 0.2 --sharpness 3.0 --seed 42 --plot

# Save as PDF
gtiv ternary --n 15 --m 3 --T 300 --save
```

This generates side-by-side ternary plots comparing voting dynamics before and after the phase transition threshold. The left plot shows dynamics before the threshold (strategic forces push outcome away from tie), while the right plot shows dynamics after the threshold (anchoring pulls outcome back toward fair tie).

### Example 16: Layer 1 Payoff Analysis

```bash
# Display payoff analysis for all time steps
gtiv strategic-reports --m 3 --n 6 --T 5 --show-payoffs

# Display payoffs only for the last time step
gtiv strategic-reports --m 3 --n 6 --T 10 --show-payoffs --payoff-time last

# Display payoffs for specific time steps
gtiv strategic-reports --m 3 --n 6 --T 10 --show-payoffs --payoff-time "1,3,5"

# With custom graph topology
gtiv strategic-reports --m 3 --n 6 --T 5 --graph "0-1,1-2,2-3" --show-payoffs

# With alphabetical output format
gtiv strategic-reports --m 3 --n 6 --T 5 --show-payoffs --alphabetical
```

The payoff analysis displays Layer 1 pairwise payoffs S^uv = <p_tilde, r_v - r_u> for each edge (u, v) in the graph, where:
- **p_tilde** = p_t - (1/m) is the centered outcome vector
- **r_u, r_v** are rank vectors (1-based: rank 1 = top preference) for voters u and v
- **S^uv** is the payoff for edge (u, v), representing the relative advantage of voter v's ranking over voter u's ranking

The output shows for each edge:
- Edge identifier (u, v)
- Rankings for both voters
- Rank vectors r_u and r_v
- Difference vector (r_v - r_u)
- Payoff value S^uv

Payoffs are computed once per time step during strategy generation and stored efficiently, making them accessible throughout the CLI workflow without recomputation. This analysis helps understand the pairwise interaction dynamics between voters in the social network.

## Project Structure

```
gtiv/
├── .github/workflows/
│   ├── python-package.yml  # Cross-platform package validation
│   └── testpypi.yml        # Manual TestPyPI publishing
├── cli/                    # CLI subcommands
├── core/                   # Simulation, aggregation, and utilities
├── docs/
│   └── PROJECT_IDENTITY.md # Project name and research terminology
├── gtiv/                   # Public Python API
├── mechanisms/             # Aggregation mechanisms
├── native/                 # Rust aggregation and optional Python extension
├── plots/                  # Plotting utilities
├── strategies/             # Voter strategies
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── explain_trajectories.py # Trajectory explanation helper
├── main.py                 # Unified `gtiv` CLI entry point
├── pyproject.toml          # Python distribution and build metadata
├── uv.lock                 # Locked development dependencies
└── verify_algorithm.py     # Algorithm verification helper
```

### Mechanism Architecture

The aggregation mechanisms are implemented as classes inheriting from `BaseMechanism`. The system automatically discovers all mechanisms in the `mechanisms/` directory:

- **BaseMechanism**: Abstract base class defining the interface for all mechanisms
- **GT**: Implements the margin-based GT method described by Rivest and Shen using a zero-sum game linear program to find a maximal lottery
- **PairwiseMajority**: Implements Pairwise Majority Rule aggregation
- **Plurality**: Implements Plurality Rule aggregation

New mechanisms can be added by creating a new class file in `mechanisms/` that inherits from `BaseMechanism`. The mechanism will be automatically discovered and available via the `--mechanism` parameter.

## Development

The package matrix exercises Python and the optional native extension on
CPython 3.12 with Ubuntu, macOS, and Windows hosted runners. To run the
Python checks from a development checkout:

```bash
python -m unittest discover -s tests -v
python verify_algorithm.py
```
