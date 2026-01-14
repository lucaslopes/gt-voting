"""
ELI5: Instantaneous vs Running Average Trajectories

Both trajectories come from a SINGLE simulation run, not multiple runs.
The difference is what they show at each time step.
"""

import numpy as np

# Example: Single simulation run with 5 time steps
# These are the instantaneous outcomes p^t at each time step
p_0 = np.array([0.33, 0.33, 0.33])  # Initial baseline (tie)
p_1 = np.array([0.40, 0.30, 0.30])  # After step 1
p_2 = np.array([0.50, 0.25, 0.25])  # After step 2
p_3 = np.array([0.60, 0.20, 0.20])  # After step 3
p_4 = np.array([0.70, 0.15, 0.15])  # After step 4

print("=" * 80)
print("INSTANTANEOUS TRAJECTORY (Gray line)")
print("=" * 80)
print("Shows the outcome p^t at each specific time step t:")
print(f"  p^0 = {p_0}  (initial baseline)")
print(f"  p^1 = {p_1}  (outcome at time 1)")
print(f"  p^2 = {p_2}  (outcome at time 2)")
print(f"  p^3 = {p_3}  (outcome at time 3)")
print(f"  p^4 = {p_4}  (outcome at time 4)")
print()
print("This is a single continuous line: p^0 → p^1 → p^2 → p^3 → p^4")
print("It shows the 'moment-by-moment' evolution, which can be jagged/chaotic.")
print()

print("=" * 80)
print("RUNNING AVERAGE TRAJECTORY (Blue line)")
print("=" * 80)
print("Shows the time-averaged outcome hat_p^t up to time t:")
print("  hat_p^t = (1/t) * sum_{τ=1}^t p^τ")
print()

# Compute running averages
hat_p_0 = p_0  # At t=0, no averaging yet, just use initial
hat_p_1 = (p_1) / 1  # Average of just p^1
hat_p_2 = (p_1 + p_2) / 2  # Average of p^1 and p^2
hat_p_3 = (p_1 + p_2 + p_3) / 3  # Average of p^1, p^2, p^3
hat_p_4 = (p_1 + p_2 + p_3 + p_4) / 4  # Average of p^1, p^2, p^3, p^4

print(f"  hat_p^0 = {hat_p_0}  (initial baseline, no averaging)")
print(f"  hat_p^1 = (p^1) / 1 = {hat_p_1}")
print(f"  hat_p^2 = (p^1 + p^2) / 2 = {hat_p_2}")
print(f"  hat_p^3 = (p^1 + p^2 + p^3) / 3 = {hat_p_3}")
print(f"  hat_p^4 = (p^1 + p^2 + p^3 + p^4) / 4 = {hat_p_4}")
print()
print("This is also a single continuous line: hat_p^0 → hat_p^1 → hat_p^2 → hat_p^3 → hat_p^4")
print("It shows the 'smoothed' evolution by averaging all outcomes up to time t.")
print("It's smoother because it averages out the fluctuations.")
print()

print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print("Both trajectories are from ONE simulation run.")
print("The running average is NOT averaging across multiple runs.")
print("Instead, it's averaging across TIME within a single run:")
print("  - At time t=1: average of just p^1")
print("  - At time t=2: average of p^1 and p^2")
print("  - At time t=3: average of p^1, p^2, and p^3")
print("  - etc.")
print()
print("This is why the running average is smoother - it's a moving average")
print("that smooths out the fluctuations in the instantaneous trajectory.")
