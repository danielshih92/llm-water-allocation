# Objective decision performance

Generate the role-balanced MR2--MR3 leaderboard from the complete multi-seed
replay:

```bash
MPLCONFIGDIR=/tmp/wacbench-matplotlib \
../venv/bin/python src/objective_outcomes/analyze_objective_outcomes.py
```

The script first averages the five fixed supply seeds and the two revised-policy
rounds within each experiment. It then macro-averages over roles and computes
95% matched experiment-cluster bootstrap intervals. Raw OF and OPF levels are
descriptive; policy-access effects are estimated from baseline-adjusted changes
by `src/adaptation_dynamics/plot_adaptation_dynamics.py`.

Outputs are written to `compare_result/objective_outcomes`, including a generated
LaTeX table so paper values do not need to be copied manually.
