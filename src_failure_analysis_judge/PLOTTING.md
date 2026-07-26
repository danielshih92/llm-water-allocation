# Failure-analysis figures

The plotting script separates the populations used by the three panels:

- Panel A uses every valid policy-round from the original seed-42 generation
  trajectories. Its mortality counts therefore match the trajectories from
  which the judged death cases were selected.
- Panel B conditions on death. Its first column is the
  deterministic fraction of source deaths that occur in a structurally
  disadvantaged role (below-median salary and above-median water
  requirement). The remaining columns use the two judges' averaged primary
  votes. Each policy label therefore receives 1 when both judges select it
  as the primary mechanism, 0.5 when one selects it, and 0 otherwise. The
  four displayed policy mechanisms are fatal
  undercommitment, winner's-curse overpayment, emergency-response failure,
  and competitive-threshold miscalibration. All percentages use model deaths
  as the denominator. Role exposure can overlap with the primary diagnosis;
  omitted no-primary and rare allocation labels mean the four displayed
  policy columns need not sum to 100.
- Panel C uses the two judges' averaged mismatch annotations among paired
  death cases. It must not be described as an all-policy mismatch rate.

From the `Alympics` project root, generate the paper figures with:

```bash
MPLCONFIGDIR=/tmp/wacbench-matplotlib \
python3 src_failure_analysis_judge/plot_failure_analysis.py \
  --input-dir judge_result/failure_analysis_full_gpt_deepseek_v3
```

The default output is the `figures` subdirectory under the input directory.
It contains a compact three-panel figure, standalone single-column figures,
their PDF versions, the exact plotted values and 95% experiment-cluster
bootstrap intervals, and a manifest recording sample coverage and panel scope.
The main paper uses only `primary_failure_with_role_heatmap.pdf`; mortality
already appears in the outcome table, while death-conditioned mismatch
results are reserved for supplementary analysis.

After checkpoint-resuming missing judge calls, run this command again to
refresh all aggregates and figures.
