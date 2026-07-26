# Policy convergence

Measure whether OF and OPF policy behavior becomes more similar across
meta-rounds without making additional API calls:

```bash
MPLCONFIGDIR=/tmp/wacbench-matplotlib \
../venv/bin/python src/policy_convergence/analyze_policy_convergence.py
```

Each admitted policy is evaluated over 144 controlled combinations of episode
stage, supply, budget, health risk, drought risk, and opponent pressure. Bids
are clamped to the feasible range and normalized by available budget. Within
each experiment, the primary convergence metric is the mean pairwise RMSE
between the five bid-response signatures. Lower distance means more similar
behavior. Normalized-AST 3-gram Jaccard similarity is a structural robustness
diagnostic rather than the primary claim.

The analysis uses the MR1 pre-feedback difference as a baseline and reports
matched experiment-cluster bootstrap intervals for MR1--MR3 changes and the
OPF-minus-OF difference in changes. Per-policy results are flushed to a JSONL
checkpoint, and the default `--resume` mode skips completed policies.

Outputs are written to `compare_result/policy_convergence`.
`policy_convergence.png` contains only the primary behavioral-distance result
at single-column dimensions. The secondary structural trajectory is written to
`policy_structure_similarity.png` for the appendix.
